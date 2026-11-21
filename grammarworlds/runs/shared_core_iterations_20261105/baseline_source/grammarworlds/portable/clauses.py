"""GF PredVP/UseCl and local weighted sentence composition."""
from dataclasses import replace
from ..grammar import seq
from .catalog import rule
from .features import Clause, NP, VP, Sentence, require
from .verbs import realize


@rule("gf.PredVP", "SentenceEng.gf", "PredVP, mkClause", tags=("clause", "subject", "agreement"))
def pred(subject: NP, predicate: VP) -> Clause:
    """Bind the subject's case/agreement features to a verb phrase."""
    require(subject, NP); require(predicate, VP)
    return Clause(subject, predicate)


@rule("gf.UseCl", "SentenceEng.gf", "UseCl", dependencies=("gf.PredVP", "gf.finite"), tags=("sentence", "tense", "negation"))
def use_cl(clause: Clause, tense="past", negative=False) -> Sentence:
    """Realize a declarative clause in simple past/present and chosen polarity."""
    require(clause, Clause)
    node = seq("gf.UseCl", clause.subject.subject,
               seq("gf.PredVP", realize(clause.predicate, clause.subject.agreement, tense, negative)))
    if negative:
        # Mentions inside a negative clause do not establish new discourse
        # antecedents outside it. Existing accessible references are unaffected.
        def scoped(n):
            label = n.label.replace("referent:", "scoped_referent:", 1) if n.label.startswith("referent:") else n.label
            return replace(n, label=label, children=tuple(scoped(c) for c in n.children) if n.kind != "text" else n.children)
        node = seq("codeco.scope", scoped(node))
    return Sentence(node)


@rule("local.ConjS", "https://www.grammaticalframework.org/lib/doc/synopsis/index.html", "ConjS (adapted)",
      tags=("coordination", "contrast", "causality", "sentence"))
def join(left: Sentence, right: Sentence, conjunction="and") -> Sentence:
    """Combine full clauses with and/but/because; never splice a clause into an NP."""
    require(left, Sentence); require(right, Sentence)
    if conjunction not in {"and", "but", "because"}:
        raise ValueError("unsupported conjunction")
    comma = "" if conjunction == "because" else ","
    return Sentence(seq("local.ConjS", left.node, comma, conjunction, right.node))


def utter(sentence: Sentence):
    require(sentence, Sentence)
    return seq("local.utterance", sentence.node, ".")
