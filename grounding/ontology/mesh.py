from __future__ import print_function
from xml.etree import cElementTree as elemtree
from datetime import date
import sys
import mappings
sys.path.append('../..')
from utils.project_config import ProjectConfig


"""
Use this to parse XML from MeSH (Medical Subject Headings). More information
on the format at: http://www.ncbi.nlm.nih.gov/mesh

End users will primarily want to call the `parse_mesh` function and do something
with the output.
"""

class Ontology:

    config = ProjectConfig()

    name = 'mesh'
    IDinit = 'D'
    def __init__(self, xml_files=[config.mesh_data_path], extend_with_umls=False):
        """ initializes the ontology instance by reading an obo_file """
        sys.stdout.write("Loading MeSH ")

        map = mappings.mapper()
        records = []

        sys.stdout.write("%s" % (" " * 11))
        sys.stdout.flush()
        sys.stdout.write("\b" * (10+1))

        for file in xml_files:
            records.extend(parse_mesh(file))
        print("")

        self.id2name = {}
        self.name2ID = {}

        for rec in records:
            id = rec.ui
            names = set()
            names.add(rec.name)
            for conc in rec.concepts:
                for term in conc.terms:
                    names.add(term.term_name)

            self.id2name[id] = names

            for name in names:
                if name not in self.name2ID:
                    self.name2ID[name] = set()
                self.name2ID[name].add(id)

            if not name.lower() in self.name2ID:
                self.name2ID[name.lower()] = set()
            self.name2ID[name.lower()].add(id)

        restricted_umls_set = set()
        for id in self.id2name.keys():
            if id in map.mesh2umls:
                restricted_umls_set.update(map.mesh2umls[id])

        if extend_with_umls:
            for id in self.id2name.keys():
                extended_lex = map.get_umls_lexicalizations(id, restrict_to=restricted_umls_set)
                print("done for", id)
                self.id2name[id].update(extended_lex)


def parse_mesh(filename):
    """Parse a mesh file, successively generating
    `DescriptorRecord` instance for subsequent processing."""

    lcounter = 0
    for _evt, elem in elemtree.iterparse(filename):
        if elem.tag == 'DescriptorRecord':
            yield DescriptorRecord.from_xml_elem(elem)

            lcounter += 1
            if lcounter % 2200  == 0:
                sys.stdout.write("#")
                sys.stdout.flush()

def date_from_mesh_xml(xml_elem):
    year = xml_elem.find('./Year').text
    month = xml_elem.find('./Month').text
    day = xml_elem.find('./Day').text
    return date(int(year), int(month), int(day))

class PharmacologicalAction(object):
    """A pharmacological action, denoting the effects of a MeSH descriptor."""

    def __init__(self, descriptor_ui):
        self.descriptor_ui = descriptor_ui

    @classmethod
    def from_xml_elem(cls, elem):
        descriptor_ui = elem.find('./DescriptorReferredTo/DescriptorUI')
        return cls(descriptor_ui)

class SlotsToNoneMixin(object):
    def __init__(self, **kwargs):
        for attr in self.__slots__:
            setattr(self, attr, kwargs.get(attr, None))

    def __repr__(self):
        attrib_repr = ', '.join(u'%s=%r' % (attr, getattr(self, attr)) for attr in self.__slots__)
        return self.__class__.__name__ + '(' + attrib_repr + ')'

class Term(SlotsToNoneMixin):
    """A term from within a MeSH concept."""

    __slots__ = ('term_ui', 'term_name', 'is_concept_preferred', 'is_record_preferred',
      'is_permuted', 'lexical_tag', 'date_created', 'thesaurus_list')

    @classmethod
    def from_xml_elem(cls, elem):
        term = cls()
        term.is_concept_preferred = elem.get('ConceptPreferredYN', None) == 'Y'
        term.is_record_preferred = elem.get('RecordPreferredYN', None) == 'Y'
        term.is_permuted = elem.get('IsPermutedTermYN', None) == 'Y'
        term.lexical_tag = elem.get('LexicalTag')
        for child_elem in elem:
            if child_elem.tag == 'TermUI':
                term.term_ui = child_elem.text
            elif child_elem.tag == 'String':
                term.term_name = child_elem.text
            elif child_elem.tag == 'DateCreated':
                term.date_created = date_from_mesh_xml(child_elem)
            elif child_elem.tag == 'ThesaurusIDlist':
                term.thesaurus_list = [th_elem.text for th_elem in child_elem]
        return term

class SemanticType(SlotsToNoneMixin):
    __slots__ = ('ui', 'name')

    @classmethod
    def from_xml_elem(cls, elem):
        sem_type = cls()
        for child_elem in elem:
            if child_elem.tag == 'SemanticTypeUI':
                sem_type.ui = child_elem.text
            elif child_elem.tag == 'SemanticTypeName':
                sem_type.name = child_elem.text

class Concept(SlotsToNoneMixin):
    """A concept within a MeSH Descriptor."""
    __slots__ = ( 'ui', 'name', 'is_preferred', 'umls_ui', 'casn1_name', 'registry_num',
      'scope_note', 'sem_types', 'terms')

    @classmethod
    def from_xml_elem(cls, elem):
        concept = cls()
        concept.is_preferred = elem.get('PreferredConceptYN', None) == 'Y'
        for child_elem in elem:
            if child_elem.tag == 'ConceptUI':
                concept.ui = child_elem.text
            elif child_elem.tag == 'ConceptName':
                concept.name = child_elem.find('./String').text
            elif child_elem.tag == 'ConceptUMLSUI':
                concept.umls_ui
            elif child_elem.tag == 'CASN1Name':
                concept.casn1_name = child_elem.text
            elif child_elem.tag == 'RegistryNumber':
                concept.registry_num = child_elem.text
            elif child_elem.tag == 'ScopeNote':
                concept.scope_note = child_elem.text
            elif child_elem.tag == 'SemanticTypeList':
                concept.sem_types = [SemanticType.from_xml_elem(st_elem)
                  for st_elem in child_elem.findall('SemanticType')]
            elif child_elem.tag == 'TermList':
                concept.terms = [Term.from_xml_elem(term_elem)
                  for term_elem in child_elem.findall('Term')]
        return concept

class DescriptorRecord(SlotsToNoneMixin):
    "A MeSH Descriptor Record."""

    __slots__ = ('ui', 'name', 'date_created', 'date_revised', 'pharm_actions',
      'tree_numbers', 'concepts')

    @classmethod
    def from_xml_elem(cls, elem):
        rec = cls()
        for child_elem in elem:
            if child_elem.tag == 'DescriptorUI':
                rec.ui = child_elem.text
            elif child_elem.tag == 'DescriptorName':
                rec.name = child_elem.find('./String').text
            elif child_elem.tag == 'DateCreated':
                rec.date_created = date_from_mesh_xml(child_elem)
            elif child_elem.tag == 'DateRevised':
                rec.date_revised = date_from_mesh_xml(child_elem)
            elif child_elem.tag == 'TreeNumberList':
                rec.tree_numbers = [tn_elem.text
                  for tn_elem in child_elem.findall('TreeNumber')]
            elif child_elem.tag == 'ConceptList':
                rec.concepts = [Concept.from_xml_elem(c_elem)
                  for c_elem in child_elem.findall('Concept')]
            elif child_elem.tag == 'PharmacologicalActionList':
                rec.pharm_actions = [PharmacologicalAction.from_xml_elem(pa_elem)
                  for pa_elem in child_elem.findall('PharmacologicalAction')]
        return rec



if __name__ == "__main__":
    mesh = Ontology()
    print(mesh.id2name["D005698"])
    print(len(mesh.id2name))
    print(len(mesh.name2ID))
    print(mesh.id2name["D046049"])

