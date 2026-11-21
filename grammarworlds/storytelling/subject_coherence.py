"""Conservative subject continuity over a composed, unsampled scene tree.

Only optional name/pronoun choices are narrowed. Physical events, claims and
authored explicit pronouns are unchanged. Alternative branches read the same
incoming context; a constructor's evaluation order cannot leak across them.
This does not infer the last subject of a previous event from its actor field.
"""
from dataclasses import replace

from ..grammar import Node
from .semantic_rules import metadata


def _subject(description):
    """An empty set means unknown, never permission to invent an antecedent."""
    kind=description.get('type')
    if kind=='entity' and description.get('entity'):
        return frozenset([description['entity']])
    if kind=='coordination':
        members=[_subject(x) for x in description.get('members',[])]
        if members and all(members):return frozenset().union(*members)
    return frozenset()


def _has_pronoun(node):
    return node.label=='gf.UsePron' or any(_has_pronoun(c) for c in node.children if isinstance(c,Node))


def _reference_choices(node, subject, allow, reference=None):
    """Edit only a clause's bound subject choices, leaving embedded scopes alone."""
    if node.label.startswith(('referent:','scoped_referent:')):
        reference=node.label.split(':',1)[1]
    if node.label=='local.reference.choice' and not allow and (not subject or reference in subject):
        kept=[(c,w) for c,w in zip(node.children,node.weights) if not _has_pronoun(c)]
        if kept:
            return replace(node,children=tuple(c for c,_ in kept),weights=tuple(w for _,w in kept))
    children=[]
    for child in node.children:
        # Nested clauses have independent reference scopes; the main walker
        # will visit them separately. Do not rewrite quoted first-person speech.
        if isinstance(child,Node) and not metadata(child).get('clause') and not child.label.startswith('dialogue.speaker:'):
            child=_reference_choices(child,subject,allow,reference)
        children.append(child)
    return replace(node,children=tuple(children))


def cohere_subjects(node):
    """Retain pronoun support only across a compatible within-scene subject.

    The first clause keeps its existing guarded reference choices because this
    pass has no cross-scene evidence. After a known subject switch, or an
    unknown/ambiguous subject, its available full-name alternative is required.
    Existing branch weights are retained; grammar expansion renormalizes each
    pruned local reference choice. No random numbers or world state are read.
    """
    def visit(current, prior):
        if current.kind=='text':return current,prior
        if current.kind=='choice':
            branches=[visit(child,prior) for child in current.children]
            return replace(current,children=tuple(n for n,_ in branches)),frozenset().union(*(p for _,p in branches))
        if current.label.startswith('dialogue.speaker:'):
            speaker=current.label.split(':',1)[1]
            # Quoted clauses can refer to their own grammatical subjects. Their
            # final subject does not become the narrator's next antecedent.
            children=[]
            for child in current.children:
                revised,_=visit(child,frozenset([None])) if isinstance(child,Node) else (child,prior)
                children.append(revised)
            return replace(current,children=tuple(children)),frozenset([frozenset([speaker])])
        clause=metadata(current).get('clause')
        subject=_subject(clause['subject']) if clause else None
        if clause:
            allowed=bool(subject) and (prior==frozenset([None]) or prior==frozenset([subject]))
            current=_reference_choices(current,subject,allowed)
        children=[];context=prior
        for child in current.children:
            if isinstance(child,Node):child,context=visit(child,context)
            children.append(child)
        return replace(current,children=tuple(children)),frozenset([subject]) if clause else context
    return visit(node,frozenset([None]))[0]


def cohere_scene(scene):
    """Return a scene with the same claims and a narrowed reference grammar."""
    return replace(scene,node=cohere_subjects(scene.node)) if scene is not None else None
