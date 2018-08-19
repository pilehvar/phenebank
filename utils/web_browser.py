from flask import Flask, render_template, request, jsonify
import os, sys
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')
sys.path.append('..')
import pipeline as pp
import nltk
from utils.entity import EntityType


# Initialize the Flask application
app = Flask(__name__)

pipe = pp.pipe()

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/_tag_sentence')
def tag_sentence():
    a = request.args.get('input', 0)

    if len(a.split(" ")) < 2:
        return {}

    a = " ".join(nltk.word_tokenize(a)) 
    bilstm_red = pipe.tag(a)

    outs = []
    for r in bilstm_red:
        for i, w in enumerate(r[0]):
            if r[2][i] is not "O":
                tag = str(r[2][i])
                outs.append("<span class='"+tag+"'>" + str(w) + "</span>")
            else:
                outs.append(str(w))

    output = " ".join(outs)
    return jsonify(result=output)

#TODO: need to add here the grounding information: from the grounding class, one can map a phenotype to its hpo class


def bulletize(names):
    out = "<ul>"
    counter = 0
    for name in names:
        counter += 1
        if counter > 5:
            continue
        out += "<li>"
        out += name
        out += "</li>"

    out += "</ul>"

    return out


def create_ann(closest):
    ann = ""

    closest = closest[0]


    if closest[0].startswith("HP:"):
        ann = "<a target='#' href='http://compbio.charite.de/hpoweb/showterm?id=" + str(closest[0]).replace("'",
                                                                                                            "") + "'>" + str(
            closest[0]).replace("'", "") + "</a> (" + str(closest[1]) + ")<br>" + bulletize(pipe.gnd.hp.id2name[closest[0]])
    elif closest[0].startswith("SCTID:"):
        ann = "<a target='#' href='http://browser.ihtsdotools.org/?perspective=full&conceptId1=" + \
              str(closest[0]).split(":")[1].replace(
                  "'",
                  "") + "'>" + str(
            closest[0]).replace("'", "") + "</a> (" + str(closest[1]) + ")<br>" + bulletize(
            pipe.gnd.snmd.id2name[closest[0]])
    elif closest[0].startswith("D"):
        ann = "<a target='#' href='https://meshb.nlm.nih.gov/record/ui?ui=" + str(closest[0]).replace("'",
                                                                                                      "") + "'>" + str(
            closest[0]).replace("'", "") + "</a> (" + str(closest[1]) + ")<br>" + bulletize(
            pipe.gnd.msh.id2name[closest[0]])

    elif closest[0].startswith("PR"):
        ann = "<a target='#' href='http://research.bioinformatics.udel.edu/pro/entry/" + str(closest[0]).replace("'",
                                                                                                  "") + "/'>" + str(
        closest[0]).replace("'", "") + "</a> (" + str(closest[1]) + ")<br>" + bulletize(
        pipe.gnd.pr.id2name[closest[0]])


    return ann


@app.route('/_tag_sentence_as_phrase')
def tag_sentence_as_phrase():
    a = request.args.get('input', 0)

    if len(a.strip().split(" ")) < 2:
        return jsonify(result="The input text must contain at least 2 words!")

    if len(a.strip().split(" ")) > 1000 or len(a.strip()) > 5000:
        return jsonify(result="Sorry! The online demo is restricted to input texts no larger than 1000 words (or 5000 characters).")

    abbreviations = pipe.get_abbrevs(a)
    paragraphs = [p for p in a.split('\n')]
 
    ais = []
    for paragraph in paragraphs: 
        ais.append(" ".join(nltk.word_tokenize(paragraph)))

    lstm_reses = []
    for ai in ais:
        if len(ai.strip()) > 0:
            lstm_o = pipe.tag(ai)
            lstm_reses.append(pipe.phrase_it(lstm_o))

    idn = 1

    outs = []
    for lstm_res in lstm_reses:
        for r in lstm_res:
            for i, w in enumerate(r[0]):
                tg = str(r[1][i])
                if tg != "O" and tg is not EntityType.Null:
                    print(w, tg)
                    tag = EntityType.get_type(tg)
                    ann = ''
                    closest = None

                    if w in abbreviations:
                        closest = pipe.ground_it(abbreviations.get(w), tag)
                    else:
                        closest = pipe.ground_it(w, tag)

                    #print w, "::", tag, closest

                    outs.append("<div class ='popup' onclick='popit(" + str(idn) + ")'>")
                    outs.append("<span class='" + tag.name + "'>" + str(w) + "</span>")

                    print(closest)
                    if closest is not None and len(closest) > 0 and closest[0][1] >= 0.9:
                        ann = create_ann(closest)
                        outs.append("<span class ='popuptext' id='myPopup" + str(idn) + "'>" + ann + "</span>")

                    outs.append("</div>")

                    idn += 1

                else:
                    outs.append(str(w))
        outs.append("<br />")            

    output = " ".join(outs)
    return jsonify(result=output)

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=int("5002"),
        debug=True,
        use_reloader=False
    )
