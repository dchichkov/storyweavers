#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/usual_goods_tusk_cautionary_adventure.py
========================================================================

A small cautionary adventure storyworld.

Seed words: usual, goods, tusk
Style: Adventure
Feature: Cautionary

Premise
-------
A child at a dockside market sees a curious tusk among ordinary goods, wants to
open the crate, and a careful adult stops them before the danger spreads. The
story can end in a safe discovery: the tusk belongs to a museum delivery, not a
treasure to handle alone.

The world is built as a tiny simulation with typed entities, physical meters,
and emotional memes. State changes drive the prose, and the child gets a clear
lesson about leaving unknown goods alone.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/usual_goods_tusk_cautionary_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/usual_goods_tusk_cautionary_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/usual_goods_tusk_cautionary_adventure.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_INIT = 5.0
CAUTION_TRAITS = {"careful", "cautious", "wise", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"risk": 0.0, "dust": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "caution": 0.0, "fear": 0.0, "relief": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    port: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    crate: str
    goods: str
    tusk_owner: str
    response: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


@dataclass
class Port:
    id: str
    place: str
    docks: str
    stalls: str
    mood: str


@dataclass
class Goods:
    id: str
    label: str
    crate_label: str
    crate_phrase: str
    danger: str
    clue: str
    movable: bool = True
    valuable: bool = True
    risky: bool = True


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


PORTS = {
    "harbor": Port("harbor", "the harbor", "wooden docks", "small stalls", "busy and salty"),
    "market": Port("market", "the market quay", "stone piers", "tarps and carts", "bright and crowded"),
}

GOODS = {
    "goods": Goods("goods", "goods", "crate", "a crate of usual goods", "might break something costly", "ordinary goods"),
    "spices": Goods("spices", "spices", "box", "a box of spices and cloth", "might spill and ruin the bundle", "packed goods"),
    "glass": Goods("glass", "glass bowls", "crate", "a crate of glass bowls", "might shatter loudly", "fragile goods"),
}

TUSKS = {
    "ivory": {"label": "tusk", "phrase": "a long tusk", "owner": "museum", "clue": "a museum tag"},
    "whale": {"label": "tusk", "phrase": "a smooth tusk", "owner": "curator", "clue": "a careful note"},
}

RESPONSES = {
    "call_adult": Response("call_adult", 3, 4,
        "called a dock worker and kept everyone back until the crate could be checked",
        "called for help, but the crate was already tipped and the mess was spreading",
        "called a dock worker and kept everyone back"),
    "step_back": Response("step_back", 4, 3,
        "stepped back and let the adults open the crate safely",
        "tried to hold the crate shut, but the lid slipped and the danger grew",
        "stepped back and let the adults open the crate"),
    "cover_goods": Response("cover_goods", 2, 2,
        "pulled a canvas over the goods and waited for a grown-up",
        "pulled a canvas over the goods, but it was too late to matter",
        "pulled a canvas over the goods and waited for a grown-up"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Ben", "Noah"]
TRAITS = ["careful", "cautious", "wise", "curious", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PORTS:
        for g in GOODS:
            for t in TUSKS:
                combos.append((p, g, t))
    return combos


def reasonableness_gate(port: Port, goods: Goods, tusk: dict) -> bool:
    return goods.risky and tusk["label"] == "tusk"


def response_ok(resp: Response) -> bool:
    return resp.sense >= 2


def severity(delay: int) -> int:
    return 2 + delay


def contained(resp: Response, delay: int) -> bool:
    return resp.power >= severity(delay)


def would_avert(trait: str) -> bool:
    return trait in CAUTION_TRAITS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary adventure about usual goods and a tusk.")
    ap.add_argument("--port", choices=PORTS)
    ap.add_argument("--goods", choices=GOODS)
    ap.add_argument("--tusk", choices=TUSKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    port = args.port or rng.choice(list(PORTS))
    goods = args.goods or rng.choice(list(GOODS))
    tusk = args.tusk or rng.choice(list(TUSKS))
    if not reasonableness_gate(PORTS[port], GOODS[goods], TUSKS[tusk]):
        raise StoryError("No story: this market choice does not create a real cautionary adventure.")
    resp = args.response or rng.choice(list(RESPONSES))
    if not response_ok(RESPONSES[resp]):
        raise StoryError("No story: that response is too weak for this cautionary world.")
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if child_gender == "boy" else "boy"
    child = args.name or _pick_name(rng, child_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=child)
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        port=port,
        child_name=child,
        child_gender=child_gender,
        helper_name=helper,
        helper_gender=helper_gender,
        crate=goods,
        goods=goods,
        tusk_owner=tusk,
        response=resp,
        trait=trait,
        delay=delay,
    )


def _do_risk(world: World) -> None:
    child = world.get("child")
    crate = world.get("crate")
    child.meters["risk"] += 1
    crate.meters["risk"] += 1
    child.memes["curiosity"] += 1


def predict(world: World) -> dict:
    sim = world.copy()
    _do_risk(sim)
    return {"risk": sim.get("crate").meters["risk"]}


def tell(params: StoryParams) -> World:
    world = World()
    port = world.add(Entity("port", "place", "port", PORTS[params.port].place))
    child = world.add(Entity("child", "character", params.child_gender, params.child_name, role="child"))
    helper = world.add(Entity("helper", "character", params.helper_gender, params.helper_name, role="helper"))
    crate = world.add(Entity("crate", "thing", "crate", GOODS[params.goods].crate_phrase, attrs={"goods": GOODS[params.goods].label}))
    tusk = world.add(Entity("tusk", "thing", "thing", TUSKS[params.tusk_owner]["phrase"], attrs={"owner": TUSKS[params.tusk_owner]["owner"]}))
    child.memes["caution"] = 1.0 if params.trait in CAUTION_TRAITS else 0.5
    helper.memes["caution"] = 2.0
    world.say(f"On a usual morning at {port.label_word}, {child.id} and {helper.id} wandered past crates of {GOODS[params.goods].clue}.")
    world.say(f"Then {child.id} spotted {tusk['phrase'] if False else TUSKS[params.tusk_owner]['phrase']} beside the usual goods.")
    world.para()
    world.say(f'“Look!” {child.id} said. “That {TUSKS[params.tusk_owner]["label"]} must be treasure!”')
    world.say(f'But {helper.id} bit {helper.pronoun("possessive")} lip. “Not so fast. Unknown goods can be risky.”')
    if would_avert(params.trait):
        child.memes["relief"] += 1
        helper.memes["relief"] += 1
        world.say(f"{child.id} listened, and the two of them kept their hands off the crate.")
        world.para()
        world.say(f"They found a dock worker, who showed them the {TUSKS[params.tusk_owner]['clue']} and explained that the {TUSKS[params.tusk_owner]['label']} was headed to a museum.")
        world.say(f"By the time they left, the ordinary goods still sat neatly packed, and the adventure had stayed safe.")
        outcome = "averted"
    else:
        world.say(f"{child.id} still wanted to open it.")
        _do_risk(world)
        world.para()
        world.say(f"The lid wobbled, and the crate shifted on the boards.")
        resp = RESPONSES[params.response]
        if contained(resp, params.delay):
            world.say(f"A dock worker came running and {resp.text}.")
            world.say("The crate was opened by grown-ups, and the tusk stayed safe inside its wrappings.")
            world.para()
            world.say(f"{helper.id} smiled and gave {child.id} a little nod. “Next time, we ask first,” {helper.pronoun('subject')} said.")
            world.say(f"That was the adventure: no treasure was lost, and no one touched goods they should not touch.")
            outcome = "contained"
        else:
            world.say(f"A dock worker came running and {resp.fail}.")
            world.say("The crate tipped, the goods scattered, and the busy quay turned into a tangle of worry.")
            world.para()
            world.say(f"{helper.id} pulled {child.id} back. “We should have left the crate alone,” {helper.pronoun('subject')} said sadly.")
            world.say("They got out safely, but the day ended with a hard lesson about strange goods and sharp tusks.")
            outcome = "burned"
    world.facts.update(params=params, child=child, helper=helper, port=port, crate=crate, tusk=tusk, outcome=outcome)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a cautionary adventure story that includes the words "usual", "goods", and "tusk".',
        f"Tell a child-friendly dock adventure where {p.child_name} sees a tusk among usual goods and learns not to touch strange cargo.",
        f"Write a short story in which a careful helper stops a child from opening packed goods that might contain a tusk.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    out = world.facts["outcome"]
    ans = [
        QAItem(question="What did the child see among the usual goods?",
               answer=f"{p.child_name} saw a tusk tucked beside the usual goods, and it looked exciting at first. But it was part of a real delivery, not something to grab alone."),
        QAItem(question="Why did the helper warn the child?",
               answer=f"The helper knew unknown goods can be risky, so {p.helper_name} told {p.child_name} not to open the crate right away. That warning kept the adventure from turning careless."),
    ]
    if out == "averted":
        ans.append(QAItem(question="How did the story end?",
                          answer=f"{p.child_name} listened, found a dock worker, and learned the tusk was going to a museum. The usual goods stayed packed, and the day ended safely."))
    else:
        resp = RESPONSES[p.response]
        ans.append(QAItem(question="How was the danger handled?",
                          answer=f"A grown-up {resp.qa_text}, so the crate stayed under control. That let everyone step back and keep the tusk and goods safe."))
    return ans


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What are goods?",
               answer="Goods are things that people carry, trade, or sell. In a market, goods are often packed in crates or boxes so they can travel safely."),
        QAItem(question="What is a tusk?",
               answer="A tusk is a long pointed tooth from some animals, like elephants. It can be valuable, so people handle it carefully."),
        QAItem(question="Why should children not open strange crates at a dock?",
               answer="Strange crates can hold heavy, sharp, or breakable things. It is safer to let a grown-up check them first."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label_word} meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(lines)


CURATED = [
    StoryParams(port="harbor", child_name="Mia", child_gender="girl", helper_name="Theo", helper_gender="boy", crate="goods", goods="goods", tusk_owner="ivory", response="call_adult", trait="careful", delay=0),
    StoryParams(port="market", child_name="Leo", child_gender="boy", helper_name="Nora", helper_gender="girl", crate="spices", goods="spices", tusk_owner="whale", response="step_back", trait="curious", delay=1),
]


ASP_RULES = r"""
valid(P,G,T) :- port(P), goods(G), tusk(T), risky(G), tusk_label(T).
safe_response(R) :- response(R), sense(R,S), min_sense(M), S >= M.
outcome(averted) :- cautious(Trait).
outcome(contained) :- not cautious(Trait), chosen_response(R), power(R,P), sev(V), P >= V.
outcome(burned) :- not cautious(Trait), chosen_response(R), power(R,P), sev(V), P < V.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PORTS:
        lines.append(asp.fact("port", p))
    for g in GOODS:
        lines.append(asp.fact("goods", g))
        lines.append(asp.fact("risky", g))
    for t in TUSKS:
        lines.append(asp.fact("tusk", t))
        lines.append(asp.fact("tusk_label", t))
    for r, obj in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, obj.sense))
        lines.append(asp.fact("power", r, obj.power))
    lines.append(asp.fact("min_sense", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_response", params.response), asp.fact("sev", severity(params.delay)), asp.fact("trait", params.trait)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP gate")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    if asp_outcome(CURATED[0]) == world_outcome(CURATED[0]):
        print("OK: ASP parity and smoke test passed.")
    else:
        rc = 1
        print("MISMATCH in outcome model.")
    return rc


def world_outcome(params: StoryParams) -> str:
    if would_avert(params.trait):
        return "averted"
    return "contained" if contained(RESPONSES[params.response], params.delay) else "burned"


def generate(params: StoryParams) -> StorySample:
    if params.port not in PORTS or params.goods not in GOODS or params.tusk_owner not in TUSKS or params.response not in RESPONSES:
        raise StoryError("Invalid story params.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
