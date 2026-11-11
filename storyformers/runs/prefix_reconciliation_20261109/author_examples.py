"""Manually authored causal examples; code supplies indices, never semantics."""
import json
from pathlib import Path
from storyformers.annotation import story_tokens
from storyformers import catalog_prefix_v3 as contract

examples = json.loads((contract.ROOT / "data/prefix_catalog_examples_v2.json").read_text())

def make(text, pos, lemma):
    spans = story_tokens(text)
    def at(token, occurrence=0):
        return [s["index"] for s in spans if s["token"] == token][occurrence]
    def anchor(kind, token, occurrence=0):
        return f"{kind}{at(token, occurrence) + 1}"
    row = dict(index=spans[-1]["index"], token=spans[-1]["token"], pos=pos, lemma=lemma, scope_id="s0")
    return row, at, anchor

def entity(name, kind="person"):
    return dict(name=name, type=kind)

def event(label, scope="s0", kind="other", factuality="asserted", **fields):
    return dict(event=label, scope_id=scope, event_type=kind, factuality=factuality, **fields)

def plot(identifier, role, stage, indices, **fields):
    return dict(plot_id=identifier, role=role, stage=stage, basis="prefix_interpretation",
                scope="observed_prefix", status="candidate", evidence_indices=indices, **fields)

def add(text, row):
    contract.validate_record(text, row)
    examples.append(dict(prefix=text, response=row))

t = "Ada wanted"
r, at, a = make(t, "v", "want")
r.update(actor="Ada", actor_id=a("e","Ada"), role="action", event="want", event_id=a("ev","wanted"),
         event_type="feel", factuality="asserted", goal_owner_id=a("e","Ada"), goal_status="proposed",
         plot=plot(a("plot","wanted"), "desire", "setup", [at("Ada"),at("wanted")], archetypes=[]),
         _references={"entities":{a("e","Ada"):entity("Ada")},
                      "events":{a("ev","wanted"):event("want",kind="feel",actor_id=a("e","Ada"))}})
add(t,r)

t = "Ada wanted to mend a kite"
r, at, a = make(t, "n", "kite")
owner, obj, scope, content = a("e","Ada"), a("e","kite"), a("s","wanted"), a("p","mend")
r.update(scope_id=scope, entity="kite",entity_id=obj,entity_name="kite", role="patient",
         event="repair object",event_id=a("ev","mend"),event_type="repair",factuality="desired",
         goal_owner_id=owner,goal_content_id=content,goal_status="active",goal_polarity="achieve",
         goal_scope_bundle=dict(owner_id=owner,intention_event_id=a("ev","wanted"),scope_id="s0",assertion_status="asserted"),
         plot=plot(a("plot","wanted"),"desire","setup",[at("wanted"),at("mend"),at("kite")],
                   goal="Mend a kite",roles={"protagonist":[owner],"central_object":[obj]},archetypes=[]),
         _references={"entities":{owner:entity("Ada"),obj:entity("kite","kite")},
            "events":{a("ev","wanted"):event("want",kind="feel",actor_id=owner),
                       a("ev","mend"):event("repair object",scope,"repair","desired",actor_id=owner,patients=[obj])},
            "scopes":{scope:dict(kind="desired",parent="s0",holder_id=owner)},
            "propositions":{content:dict(content="Ada mends a kite",polarity="positive",scope_id=scope)}})
add(t,r)

t = "Nora’s compass fell. Nora"
r, at, a = make(t,"n","Nora")
r.update(entity="person",entity_id=a("e","Nora’s"),entity_name="Nora",antecedent_id=a("e","Nora’s"),
         _references={"entities":{a("e","Nora’s"):entity("Nora")}})
add(t,r)

t = "Ivo told Ana, “Borrow"
r, at, a = make(t,"v","borrow")
speaker, actor, scope, ev = a("e","Ivo"),a("e","Ana"),a("q","“"),a("ev","Borrow")
r.update(scope_id=scope,actor="Ana",actor_id=actor,speaker_id=speaker,addressee_ids=[actor],
         mood="imperative",imperative_subject_status="understood_addressee",patients=[],instruments=[],
         role="action",event="obtain object",event_id=ev,event_type="obtain",factuality="desired",
         speech_act_kind="instruction",quote_mode="direct",assertion_status="attributed_claim",
         _references={"entities":{speaker:entity("Ivo"),actor:entity("Ana")},
                      "scopes":{scope:dict(kind="quotation",parent="s0",speaker_id=speaker)},
                      "events":{ev:event("obtain object",scope,"obtain","desired",actor_id=actor,patients=[],instruments=[])}})
add(t,r)

t = "Mika said, “I can walk.” Jo said, “Not safely"
r, at, a = make(t,"adv","safely")
quote, neg, jo, content = a("q","“",1),a("s","Not"),a("e","Jo"),a("p","safely")
r.update(scope_id=neg,speaker_id=jo,quote_mode="direct",speech_act_kind="safety_objection",
         utterance_content_id=content,verb_phrase_ellipsis=True,assertion_status="attributed_claim",
         _references={"entities":{jo:entity("Jo")},
                      "scopes":{quote:dict(kind="quotation",parent="s0",speaker_id=jo),neg:dict(kind="negation",parent=quote)},
                      "propositions":{content:dict(content="The proposed walking is not safe",polarity="negative",scope_id=quote)}})
add(t,r)

t = "Rosa promised to return the brush"
r, at, a = make(t,"n","brush")
owner,obj,scope,content=a("e","Rosa"),a("e","brush"),a("s","promised"),a("p","return")
r.update(scope_id=scope,entity="brush",entity_id=obj,entity_name="brush",event="return object",
         event_id=a("ev","return"),role="patient",factuality="desired",promise_content_id=content,
         plan_commitment_status="promised",obligation_debtor_id=owner,obligation_content_id=content,
         obligation_status="promised",plot=plot(a("plot","promised"),"promise","setup",[at("promised"),at("return"),at("brush")]),
         _references={"entities":{owner:entity("Rosa"),obj:entity("brush","brush")},
                      "events":{a("ev","return"):event("return object",scope,"transfer","desired",actor_id=owner,patients=[obj])},
                      "scopes":{scope:dict(kind="promised",parent="s0",holder_id=owner)},
                      "propositions":{content:dict(content="Rosa returns the brush",polarity="positive",scope_id=scope)}})
add(t,r)

t = "Omar wanted a stamp. The stamp filled his last empty square"
r, at, a = make(t,"n","square")
owner,stamp,square=a("e","Omar"),a("e","stamp"),a("e","square")
goal,prior,ev=a("p","wanted"),a("ev","wanted"),a("ev","filled")
r.update(entity="card_square",entity_id=square,entity_name="square",goal_owner_id=owner,
         goal_content_id=goal,goal_status="achieved",event="fill square",event_id=ev,role="destination",
         narrative_resolution_evidence=dict(problem=goal,outcome=ev,status="explicitly_closed"),
         plot=plot(a("plot","wanted"),"payoff","resolution",[at("wanted"),at("filled"),at("square")],
                   goal="Obtain a stamp",roles={"protagonist":[owner]},
                   incoming_links=[dict(source_event=prior,relation="payoff_of",basis="prefix_interpretation",mechanically_verified=False)]),
         _references={"entities":{owner:entity("Omar"),stamp:entity("stamp","stamp"),square:entity("square","card_square")},
                      "events":{prior:event("want",kind="feel",actor_id=owner),ev:event("fill square",patients=[square])},
                      "propositions":{goal:dict(content="Omar obtains a stamp",polarity="positive",scope_id="s0")}})
add(t,r)

t = "A bird sat by Mei. Mei drew it in a book. The book showed a bird"
r, at, a = make(t,"n","bird")
real,carrier,image,scope=a("e","bird"),a("e","book"),a("e","bird",1),a("s","showed")
r.update(scope_id=scope,entity="depicted_bird",entity_id=image,entity_name="drawn bird",
         depiction=dict(carrier_id=carrier,image_entity_id=image,referent_id=real,medium="drawing",scope_id=scope),
         _references={"entities":{real:entity("bird","bird"),carrier:entity("book","book"),image:entity("drawn bird","depicted_bird")},
                      "scopes":{scope:dict(kind="depiction",parent="s0")}})
add(t,r)

t = "Tao thought the box was empty"
r, at, a = make(t,"adj","empty")
owner,scope,content=a("e","Tao"),a("s","thought"),a("p","was")
r.update(scope_id=scope,belief_holder_id=owner,epistemic_attitude_kind="belief",belief_content_id=content,
         belief_polarity="accepts",epistemic_content_binding_status="resolved",
         epistemic_scope_bundle=dict(holder_id=owner,attitude_event_id=a("ev","thought"),scope_id="s0",assertion_status="asserted"),
         _references={"entities":{owner:entity("Tao")},
                      "events":{a("ev","thought"):event("think",kind="feel",actor_id=owner)},
                      "scopes":{scope:dict(kind="belief",parent="s0",holder_id=owner)},
                      "propositions":{content:dict(content="The box is empty",polarity="positive",scope_id=scope)}})
add(t,r)

contract.EXAMPLES.write_text(json.dumps(examples,indent=2,ensure_ascii=False)+"\n")
print(f"Saved {len(examples)} validated examples")
