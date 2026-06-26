#!/usr/bin/env python3
"""
storyworlds/worlds/nervous_suspense_myth.py
===========================================

A compact mythic storyworld about a nervous child, a sacred object at risk,
and a suspenseful, wise compromise.

The premise is classical and small:
- A young hero loves a mythic task.
- The task would endanger a treasured item.
- An elder sees the risk, the hero grows nervous, and a safer sacred tool is
  chosen.
- The ending image proves the change in the world state.

This world is intentionally narrow: only combinations that make a believable
mythic warning and a believable protection are generated.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def _g(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def _m(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self._g(key) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self._m(key) + amount

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "oracle"}
        male = {"boy", "father", "man", "keeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Realm:
    name: str
    dusk: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    atmosphere: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Aid:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, realm: Realm) -> None:
        self.realm = realm
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.atmosphere: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.realm)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.atmosphere = self.atmosphere
        clone.paragraphs = [[]]
        return clone


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_aid(action: Action, prize: Prize) -> Optional[Aid]:
    for aid in AIDS:
        if action.mess in aid.guards and prize.region in aid.covers:
            return aid
    return None


@dataclass
class Rule:
    name: str
    apply: callable


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in {a.mess for a in ACTIONS.values()}:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.add_meter(mess)
                item.add_meter("dirty")
                out.append(f"{actor.id}'s {item.label} grew {mess} and dirty.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("dirty", 0.0) < THRESHOLD or not ent.caretaker:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        keeper = world.get(ent.caretaker)
        keeper.add_meter("worry")
        out.append(f"That would bring more work for {keeper.label}.")
    return out


CAUSAL_RULES = [Rule("soil", _r_soil), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "worry": sum(e.meters.get("worry", 0.0) for e in sim.characters()),
    }


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.realm.affords:
        return
    world.zone = set(action.zone)
    actor.add_meter(action.mess)
    actor.add_meme("joy")
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"{hero.id} was a little {trait} {hero.type} who listened for old tales in the wind.")


def love_act(world: World, hero: Entity, action: Action) -> None:
    hero.add_meme("love")
    world.say(f"{hero.pronoun().capitalize()} loved {action.gerund}; in the dusk it felt like stepping into a story.")


def gift(world: World, keeper: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One evening, {hero.id}'s {keeper.type} gave {hero.pronoun('object')} {prize.phrase}.")


def cherish(world: World, hero: Entity, prize: Entity) -> None:
    hero.add_meme("love")
    prize.worn_by = hero.id
    world.say(f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} like a blessing.")


def arrive(world: World, hero: Entity, elder: Entity, action: Action) -> None:
    world.say(f"One dusk, {hero.id} and {hero.pronoun('possessive')} {elder.label} went to {world.realm.name}.")
    world.say(f"The air was {world.atmosphere or action.atmosphere}, and every leaf seemed to hold its breath.")


def want(world: World, hero: Entity, action: Action) -> None:
    hero.add_meme("desire")
    hero.add_meme("nervous")
    world.say(f"{hero.id} wanted to {action.verb}, but {hero.pronoun('subject')} felt nervous at the edge of the dark path.")


def warn(world: World, elder: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    pred = predict_mess(world, hero, action, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = action.soil
    world.facts["predicted_worry"] = pred["worry"]
    clause = f"You'll get your {prize.label} {action.soil}"
    if pred["worry"] >= THRESHOLD:
        clause += ", and then there will be more work"
    world.say(f"'{clause},' {elder.label} said softly. 'Let us choose another way.'")
    return True


def hesitate(world: World, hero: Entity, action: Action) -> None:
    hero.add_meme("nervous")
    world.say(f"{hero.id} swallowed hard, then reached toward the shadowy trail anyway.")


def risk_step(world: World, elder: Entity, hero: Entity, action: Action) -> None:
    world.say(f"But {hero.pronoun('possessive')} {elder.label} lifted a hand and stopped {hero.pronoun('object')}.")


def compromise(world: World, elder: Entity, hero: Entity, action: Action, prize: Entity) -> Optional[Aid]:
    aid_def = select_aid(action, prize)
    if aid_def is None:
        return None
    aid = world.add(Entity(id=aid_def.id, type="aid", label=aid_def.label, owner=hero.id, caretaker=elder.id,
                           protective=True, covers=set(aid_def.covers), plural=aid_def.plural))
    aid.worn_by = hero.id
    if predict_mess(world, hero, action, prize.id)["soiled"]:
        aid.worn_by = None
        del world.entities[aid.id]
        return None
    world.say(f"{hero.pronoun('possessive').capitalize()} {elder.label} smiled and said, 'How about we {aid_def.prep} and {action.verb} together?'")
    return aid_def


def accept(world: World, elder: Entity, hero: Entity, action: Action, prize: Entity, aid_def: Aid) -> None:
    hero.add_meme("joy")
    hero.add_meme("love")
    hero.memes["nervous"] = 0.0
    world.say(f"{hero.id} nodded, and {hero.pronoun('subject')} hugged {hero.pronoun('possessive')} {elder.label}.")
    world.say(f"They {aid_def.tail}. Soon {hero.id} was {action.gerund}, {prize_was_safe(hero, prize)}, and the dusk felt kind.")


def prize_was_safe(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed bright and clean"


def tell(realm: Realm, action: Action, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, elder_type: str = "keeper") -> World:
    world = World(realm)
    world.atmosphere = action.atmosphere

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["nervous", "curious"])))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="elder"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=elder.id, region=prize_cfg.region, plural=prize_cfg.plural))

    intro(world, hero)
    love_act(world, hero, action)
    gift(world, elder, hero, prize)
    cherish(world, hero, prize)

    world.para()
    arrive(world, hero, elder, action)
    want(world, hero, action)
    warn(world, elder, hero, action, prize)
    hesitate(world, hero, action)
    risk_step(world, elder, hero, action)

    world.para()
    aid_def = compromise(world, elder, hero, action, prize)
    if aid_def:
        accept(world, elder, hero, action, prize, aid_def)

    world.facts.update(hero=hero, elder=elder, prize=prize, prize_cfg=prize_cfg, action=action,
                       realm=realm, aid=aid_def, conflict=hero.meters.get("nervous", 0.0) >= THRESHOLD,
                       resolved=aid_def is not None)
    return world


REALMS = {
    "moon_gate": Realm(name="the Moon Gate", affords={"cross_bridge", "light_beacon"}),
    "river_temple": Realm(name="the river temple", affords={"cross_bridge", "light_beacon"}),
    "forest_shrine": Realm(name="the forest shrine", affords={"enter_cave", "light_beacon"}),
}


ACTIONS = {
    "cross_bridge": Action(
        id="cross_bridge",
        verb="cross the bridge",
        gerund="crossing the bridge",
        rush="run onto the bridge",
        mess="wind",
        soil="blown into trouble",
        zone={"head", "torso"},
        atmosphere="cold and trembling",
        keyword="bridge",
        tags={"bridge", "wind"},
    ),
    "enter_cave": Action(
        id="enter_cave",
        verb="enter the cave",
        gerund="entering the cave",
        rush="step into the cave",
        mess="darkness",
        soil="lost in the dark",
        zone={"feet", "torso"},
        atmosphere="quiet and echoing",
        keyword="cave",
        tags={"cave", "darkness"},
    ),
    "light_beacon": Action(
        id="light_beacon",
        verb="light the beacon",
        gerund="lighting the beacon",
        rush="strike the flint",
        mess="sparks",
        soil="scorched by sparks",
        zone={"torso", "hands"},
        atmosphere="blue and still",
        keyword="beacon",
        tags={"fire", "light"},
    ),
}


AIDS = [
    Aid(
        id="cloak",
        label="a wind-cloak",
        covers={"torso", "head"},
        guards={"wind"},
        prep="wrap yourself in the wind-cloak first",
        tail="wrapped the wind-cloak close and crossed the bridge safely",
    ),
    Aid(
        id="lamp",
        label="a lantern-lamp",
        covers={"torso", "feet"},
        guards={"darkness"},
        prep="carry a lantern-lamp first",
        tail="held the lantern-lamp high and went through the cave safely",
    ),
    Aid(
        id="glove",
        label="spark-gloves",
        covers={"hands"},
        guards={"sparks"},
        prep="put on spark-gloves first",
        tail="put on the spark-gloves and lit the beacon without harm",
        plural=True,
    ),
]


PRIZES = {
    "torch": Prize(label="torch", phrase="a bright torch of cedar wood", type="torch", region="torso"),
    "cloak": Prize(label="cloak", phrase="a silver cloak", type="cloak", region="torso"),
    "feather": Prize(label="feather", phrase="a sacred feather", type="feather", region="head"),
    "ring": Prize(label="ring", phrase="a bronze ring", type="ring", region="hands"),
}


GIRL_NAMES = ["Ari", "Nia", "Luna", "Mira", "Sera", "Iris"]
BOY_NAMES = ["Kai", "Taro", "Eli", "Milo", "Oren", "Noel"]
TRAITS = ["brave", "gentle", "curious", "earnest", "steady", "small"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for realm_name, realm in REALMS.items():
        for act_id in realm.affords:
            act = ACTIONS[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_aid(act, prize):
                    combos.append((realm_name, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    realm: str
    action: str
    prize: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "bridge": [("What is a bridge?", "A bridge is a path built over water, a road, or a gap so people can cross safely.")],
    "cave": [("What is a cave?", "A cave is a hollow space in rock, often dark and cool inside.")],
    "wind": [("What is wind?", "Wind is moving air. It can push leaves, shake branches, and make clothes flutter.")],
    "darkness": [("Why do people carry a light in the dark?", "A light helps people see where to step and keeps them from bumping into things.")],
    "sparks": [("What are sparks?", "Sparks are tiny bits of fire that flash for a moment when flint or metal strikes.")],
    "torch": [("What is a torch?", "A torch is a burning stick or lamp used to give light.")],
    "cloak": [("What is a cloak?", "A cloak is a loose garment that covers the shoulders and body, often to keep warm.")],
    "feather": [("What is a feather?", "A feather is the soft covering on a bird's body that helps it fly and stay warm.")],
    "ring": [("What is a ring?", "A ring is a small loop of metal worn on a finger or used as a special symbol.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, act, prize = f["hero"], f["elder"], f["action"], f["prize_cfg"]
    return [
        f'Write a short mythic story for a small child about a nervous {hero.type} named {hero.id} and a sacred {prize.label}.',
        f"Tell a suspenseful tale where {hero.id} wants to {act.verb}, but {hero.pronoun('possessive')} {elder.label} knows a safer way.",
        f'Write a simple myth with the word "{act.keyword}" and an ending where the hero chooses the wiser path.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, act = f["hero"], f["elder"], f["prize"], f["action"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} goes to {world.realm.name}?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} and {hero.pronoun('possessive')} {elder.label}. They walk into {world.realm.name} with a sacred {prize.label}.",
        ),
        QAItem(
            question=f"What did {trait} {hero.id} want to do at {world.realm.name}?",
            answer=f"{trait.capitalize()} {hero.id} wanted to {act.verb}. It felt exciting, but the task was risky for {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"Why was {hero.id} nervous before the journey?",
            answer=f"{hero.id} was nervous because the path looked dangerous and {hero.pronoun('possessive')} {prize.label} could be harmed if {hero.pronoun('subject')} went the wrong way.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did {hero.id}'s {elder.label} warn {hero.id} about {act.verb}?",
            answer=f"{hero.pronoun('possessive').capitalize()} {elder.label} warned {hero.id} because a trial like that would make {hero.pronoun('possessive')} {prize.label} get {f.get('predicted_soil', 'ruined')}.",
        ))
    if f.get("resolved"):
        aid = f["aid"]
        qa.append(QAItem(
            question=f"How did {aid.label} help {hero.id} {act.verb} safely?",
            answer=f"They used {aid.label} first, and that protected the right part of {hero.id}'s body. So {hero.id} could {act.verb} without ruining {hero.pronoun('possessive')} {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt calm and happy at the end. The nervous feeling faded, and the hero was able to {act.gerund} while {hero.pronoun('possessive')} {prize.label} stayed safe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    if world.facts.get("aid"):
        tags.add(world.facts["aid"].id)
    if world.facts.get("prize"):
        tags.add(world.facts["prize"].label)
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in {tuple(x[:2]) for x in world.fired})}")
    return "\n".join(lines)


def explain_rejection(action: Action, prize: Prize) -> str:
    if not prize_at_risk(action, prize):
        return f"(No story: {action.gerund} does not threaten a {prize.label} in this world.)"
    return f"(No story: there is no fitting sacred aid for a {prize.label} against {action.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s object here; try {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic suspense storyworld with a nervous hero.")
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["keeper", "oracle"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.prize:
        act, prize = ACTIONS[args.action], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_aid(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.realm is None or c[0] == args.realm)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    realm, action, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["keeper", "oracle"])
    trait = rng.choice(TRAITS)
    return StoryParams(realm=realm, action=action, prize=prize, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(REALMS[params.realm], ACTIONS[params.action], PRIZES[params.prize], params.name, params.gender, [params.trait, "nervous"], params.elder)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(realm="moon_gate", action="cross_bridge", prize="torch", name="Ari", gender="girl", elder="oracle", trait="curious"),
    StoryParams(realm="forest_shrine", action="enter_cave", prize="cloak", name="Kai", gender="boy", elder="keeper", trait="steady"),
    StoryParams(realm="river_temple", action="light_beacon", prize="ring", name="Mira", gender="girl", elder="keeper", trait="earnest"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
protects(A,P,G) :- prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(A,P,_).
valid(Realm,A,P) :- affords(Realm,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Realm,A,P,G) :- valid(Realm,A,P), wears(G,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, realm in REALMS.items():
        lines.append(asp.fact("realm", rid))
        for a in sorted(realm.affords):
            lines.append(asp.fact("affords", rid, a))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for z in sorted(act.zone):
            lines.append(asp.fact("zone", aid, z))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        if prize.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(prize.genders):
            lines.append(asp.fact("wears", g, pid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for m in sorted(aid.guards):
            lines.append(asp.fact("guards", aid.id, m))
        for c in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (realm, action, prize) combos ({len(stories)} with gender):\n")
        for realm, action, prize in triples:
            genders = sorted(g for (r, a, p, g) in stories if (r, a, p) == (realm, action, prize))
            print(f"  {realm:12} {action:12} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.realm} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
