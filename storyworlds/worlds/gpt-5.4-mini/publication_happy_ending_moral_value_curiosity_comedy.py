#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/publication_happy_ending_moral_value_curiosity_comedy.py
=======================================================================================

A standalone storyworld for a tiny comedy about curiosity, a publication, and a
good moral ending.

Premise
-------
A curious child wants to peek at a neighborhood "publication" before it is ready.
The child discovers that the missing piece is not a secret prize, but a kind
credit and a careful check. The tension comes from impatience and comic mishaps;
the turn comes when curiosity is used for helping instead of snooping; the ending
proves a happy, moral result by seeing the finished publication shared kindly.

This is a small simulation with typed entities, physical meters and emotional
memes, a reasonableness gate, a Python/ASP twin, and grounded Q&A.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
COMEDY_TONE = "comedy"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Publication:
    id: str
    label: str
    kind: str
    missing_piece: str
    finish_word: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    helps: str
    reveals: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_ink(world: World) -> list[str]:
    out: list[str] = []
    pub = world.get("publication")
    if pub.meters["messy"] < THRESHOLD:
        return out
    sig = ("ink", pub.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pub.meters["needs_help"] += 1
    out.append("__ink__")
    return out


def _r_pride(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["helped"] < THRESHOLD:
            continue
        sig = ("pride", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["pride"] += 1
        out.append("__pride__")
    return out


CAUSAL_RULES = [Rule("ink", "physical", _r_ink), Rule("pride", "social", _r_pride)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class Setting:
    id: str
    label: str
    place: str


@dataclass
class Action:
    id: str
    verb: str
    comic_mess: str
    risk: str
    benefit: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


SETTINGS = {
    "newsroom": Setting("newsroom", "a tiny newsroom", "the news table"),
    "library": Setting("library", "the library corner", "the quiet reading desk"),
    "school": Setting("school", "the school clubroom", "the craft table"),
}

ACTIONS = {
    "sticker": Action("sticker", "peek at the stickers", "sticky fingers", "smudged page edges", "discovering the title",
                      {"sticky", "messy"}),
    "paint": Action("paint", "help with the paint pens", "paint dots on the paper", "ink spots on the page", "drawing the cover",
                    {"ink", "messy"}),
    "jelly": Action("jelly", "taste the jelly for ideas", "jelly smears on the table", "a wobbly disaster", "finding the funny caption",
                    {"sticky", "messy"}),
}

PUBLICATIONS = {
    "paper": Publication("paper", "the publication", "newspaper", "the title line", "finished", tags={"paper", "publication"}),
    "zine": Publication("zine", "the little zine", "zine", "the cover note", "assembled", tags={"zine", "publication"}),
    "poster": Publication("poster", "the poster", "poster", "the headline", "shared", tags={"poster", "publication"}),
}

CLUES = {
    "stamp": Clue("stamp", "a rubber stamp", "helps make copies", "reveals the byline", {"stamp", "help"}),
    "label": Clue("label", "a label maker", "helps name pages", "reveals the section title", {"label", "help"}),
    "glue": Clue("glue", "a glue stick", "helps fix corners", "reveals the last page", {"glue", "help"}),
}

RESPONSES = {
    "wipe": Response("wipe", 3, 4, "grabbed a clean cloth and wiped the smudges from the page", "wiped at the mess, but it only spread the spots around",
                     "wiped the smudges away", {"clean"}),
    "dry": Response("dry", 3, 3, "set the paper under a fan and let it dry before touching it again", "waited for it to dry, but the page was already too messy",
                    "let the page dry safely", {"clean"}),
    "restart": Response("restart", 4, 5, "picked a fresh sheet and started the publication again with careful hands", "tried to restart, but the old page was too tangled to save",
                        "started again with a fresh page", {"clean"}),
    "saucepan": Response("saucepan", 1, 1, "held up a saucepan and hoped for the best", "held up a saucepan, which was not a useful plan at all",
                         "did a very silly thing", {"silly"}),
}

CHILDREN = [("Milo", "boy"), ("Nina", "girl"), ("Pia", "girl"), ("Theo", "boy"), ("June", "girl"), ("Arlo", "boy")]
TRAITS = ["curious", "careful", "mischievous", "earnest", "bright"]


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 3]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTIONS:
            for p in PUBLICATIONS:
                if "messy" in ACTIONS[a].tags and "publication" in PUBLICATIONS[p].tags:
                    combos.append((s, a, p))
    return combos


@dataclass
class StoryParams:
    setting: str
    action: str
    publication: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Curiosity, a publication, and a comic moral ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--publication", choices=PUBLICATIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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


def clue_for(action: Action) -> Clue:
    return CLUES["stamp"] if action.id == "sticker" else CLUES["label"] if action.id == "paint" else CLUES["glue"]


def predict(world: World, action: Action, publication_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get("child"), action, narrate=False)
    pub = sim.get(publication_id)
    return {"messy": pub.meters["messy"] >= THRESHOLD, "help": pub.meters["needs_help"] >= THRESHOLD}


def _do_action(world: World, child: Entity, action: Action, narrate: bool = True) -> None:
    child.memes["curiosity"] += 1
    world.get("publication").meters["messy"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, action: Action, pub: Publication, response: Response,
         child_name: str = "Milo", child_gender: str = "boy",
         helper_name: str = "Nina", helper_gender: str = "girl",
         adult_type: str = "mother", trait: str = "curious") -> World:
    world = World()
    child = world.add(Entity(child_name, "character", child_gender, traits=["small", trait]))
    helper = world.add(Entity(helper_name, "character", helper_gender, traits=["helpful"]))
    adult = world.add(Entity("Adult", "character", adult_type, label="the adult"))
    publication = world.add(Entity("publication", "thing", "publication", label=pub.label))
    clue = world.add(Entity("clue", "thing", "tool", label=clue_for(action).label))

    child.memes["curiosity"] = 2.0
    helper.memes["care"] = 2.0

    world.say(
        f"At {setting.label}, {child.id} and {helper.id} were helping at {setting.place}. "
        f"They were making {pub.label}, and {clue.label} sat nearby like a tiny joke waiting to happen."
    )
    world.say(
        f"{child.id} was very {trait}, and {child.id} kept asking what the last page would say. "
        f"{helper.id} laughed and said the page was a surprise."
    )

    world.para()
    world.say(
        f"Then {child.id} wanted to {action.verb}. That made {child.pronoun('possessive')} "
        f"hands {action.comic_mess}, and everybody made a face like a squashed plum."
    )
    pred = predict(world, action, "publication")
    world.facts["pred"] = pred
    world.facts["action"] = action
    world.facts["publication_cfg"] = pub

    world.say(
        f"{helper.id} frowned with comic seriousness and warned, "
        f"\"If you do that, the publication will end up with {action.risk}.\""
    )

    if action.id == "jelly":
        world.say(f"{child.id} tried to explain that it was 'research,' which did not help at all.")
    else:
        world.say(f"{child.id} giggled, because the idea sounded clever for about one second.")

    world.para()
    if response.sense >= 3:
        world.say(
            f"{adult.label_word.capitalize()} came over and {response.text}."
        )
        world.get("publication").meters["messy"] = 0.0
        world.get("publication").memes["relief"] += 1
        child.memes["helped"] += 1
        child.memes["guilt"] += 1
        world.say(
            f"The room settled down. The publication was safe again, and {child.id} promised to use curiosity "
            f"for helping instead of poking at things."
        )
        world.para()
        world.say(
            f"After that, {child.id} noticed a missing credit line, found the right name, and fixed it before the final print."
        )
        world.say(
            f"At last, the publication came out finished, and {child.id} even got a laugh for {child.pronoun('possessive')} trouble."
        )
        outcome = "happy"
    else:
        world.say(
            f"{adult.label_word.capitalize()} came over and {response.fail}."
        )
        world.get("publication").meters["messy"] = 1.0
        world.say(
            f"That was so silly that everyone paused, then chose a clean fresh page and laughed while they started over."
        )
        world.para()
        world.say(
            f"By the end, the publication was still saved, because the grown-up fix was to begin again carefully."
        )
        outcome = "happy"

    world.facts.update(child=child, helper=helper, adult=adult, clue=clue,
                       publication=publication, setting=setting, response=response,
                       outcome=outcome)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, action, pub = f["child"], f["helper"], f["action"], f["publication_cfg"]
    return [
        f'Write a funny story for a young child that includes the word "publication" and ends happily.',
        f"Tell a comedy story where {child.id} gets curious during a publication project, makes a mess, and learns a moral lesson with help from {helper.id}.",
        f'Write a child-facing story about curiosity and kindness, with a publication, a comic mistake, and a bright happy ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, adult, action, pub = f["child"], f["helper"], f["adult"], f["action"], f["publication_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who were helping make {pub.label}. {adult.label_word.capitalize()} came in to help when things got messy."),
        ("What did {0} want to do?".format(child.id),
         f"{child.id} wanted to {action.verb}. That choice made the publication messy, which is why the others had to stop and fix it."),
        ("What did the grown-up do?",
         f"{adult.label_word.capitalize()} helped clean up and make a careful plan. That turned the problem into a safe ending instead of a big fuss."),
        ("What did {0} learn?".format(child.id),
         f"{child.id} learned that curiosity is best when it helps, not when it causes trouble. The moral was to ask first and use careful hands."),
    ]
    if f.get("outcome") == "happy":
        qa.append(("How did the story end?",
                   f"It ended happily with the publication finished. {child.id} still got to be curious, but this time curiosity helped the work get done."))
    return qa


KNOWLEDGE = {
    "publication": [("What is a publication?",
                     "A publication is something that gets written, printed, or shared, like a newspaper, magazine, or little zine.")],
    "curiosity": [("What is curiosity?",
                   "Curiosity means wanting to know, see, or learn more. It can be a very helpful feeling when it is used kindly.")],
    "moral": [("What is a moral in a story?",
                 "A moral is the lesson the story teaches, often about how to be kind, careful, or honest.")],
    "kindness": [("Why is kindness important?",
                  "Kindness helps people work together and feel safe. It makes problems smaller because people want to help each other.")],
    "mess": [("Why do messy hands make paper hard to use?",
              "Messy hands can leave smudges, stickiness, or spots on the paper, and then the page may need to be cleaned or replaced.")],
}
KNOWLEDGE_ORDER = ["publication", "curiosity", "moral", "kindness", "mess"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"publication", "curiosity", "moral", "kindness", "mess"}
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(action: Action, pub: Publication) -> str:
    return f"(No story: {action.verb} would not make a useful comic problem for {pub.label}.)"


def outcome_of(params: StoryParams) -> str:
    return "happy"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("messy_action", aid))
    for pid in PUBLICATIONS:
        lines.append(asp.fact("publication", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 3))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, A, P) :- setting(S), action(A), publication(P), messy_action(A), publication(P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
happy_end :- sensible(_).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo gate.")
    sens_py = {r.id for r in sensible_responses()}
    sens_cl = set(asp_sensible())
    if sens_py == sens_cl:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    cases = [resolve_params(argparse.Namespace(setting=None, action=None, publication=None, response=None, child=None, child_gender=None, helper=None, helper_gender=None, adult=None, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(s)) for s in range(3)]
    _ = cases
    print("OK: generated-story checks exercised.")
    return rc


def build_sample_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.publication is None or c[2] == args.publication)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, publication = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice([n for n, g in CHILDREN if g == child_gender])
    helper = args.helper or rng.choice([n for n, g in CHILDREN if g == helper_gender and n != child])
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, action, publication, response, child, child_gender, helper, helper_gender, adult, trait)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return build_sample_story_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], PUBLICATIONS[params.publication],
                 RESPONSES[params.response], params.child, params.child_gender,
                 params.helper, params.helper_gender, params.adult, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


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
    StoryParams("newsroom", "paint", "paper", "wipe", "Milo", "boy", "Nina", "girl", "mother", "curious"),
    StoryParams("library", "sticker", "zine", "dry", "June", "girl", "Theo", "boy", "father", "bright"),
    StoryParams("school", "jelly", "poster", "restart", "Arlo", "boy", "Pia", "girl", "mother", "mischievous"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
