#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/appetizing_surprise_comedy.py
==============================================================

A tiny standalone story world for an appetizing surprise comedy:
a child tries to make a delicious surprise snack, a silly mix-up creates
brief worry, and the ending lands on a warm, funny reveal.

The world keeps the story small and classical:
- typed entities with physical meters and emotional memes
- forward-chained causal rules
- a reasonableness gate plus an ASP twin
- three Q&A sets grounded in the simulated world state
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    likes_sweet: bool = False
    likes_fruit: bool = False
    can_smell: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    appetizing: bool = True
    surprise_kind: str = "sweet"
    secret: str = ""
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    rescue: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_smell(world: World) -> list[str]:
    out: list[str] = []
    for snack in list(world.entities.values()):
        if snack.kind != "thing" or snack.meters["fresh"] < THRESHOLD:
            continue
        sig = ("smell", snack.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "kitchen" in world.entities:
            world.get("kitchen").meters["appetizing"] += 1
        for c in world.characters():
            c.memes["curiosity"] += 1
        out.append("__smell__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for snack in list(world.entities.values()):
        if snack.kind != "thing" or snack.meters["messy"] < THRESHOLD:
            continue
        sig = ("spill", snack.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.characters():
            c.memes["surprise"] += 1
        out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("smell", "physical", _r_smell), Rule("spill", "social", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            msgs = rule.apply(world)
            if msgs:
                changed = True
                produced.extend(m for m in msgs if not m.startswith("__"))
    if narrate:
        for msg in produced:
            world.say(msg)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for snack_id, snack in SNACKS.items():
            for response_id, resp in RESPONSES.items():
                if snack.appetizing and resp.sense >= SENSE_MIN:
                    combos.append((scene.id, snack_id, response_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def story_type_of(snack: Snack) -> str:
    return "sweet" if snack.surprise_kind == "sweet" else "savory"


def _do_sneaky(world: World, snack: Entity, narrate: bool = True) -> None:
    snack.meters["hidden"] += 1
    snack.meters["fresh"] += 1
    propagate(world, narrate=narrate)


def smell(world: World, snack: Snack, child: Entity) -> None:
    world.say(
        f"The kitchen smelled {snack.label}, and that made {child.id}'s nose twitch. "
        f"It was already starting to feel like a happy surprise."
    )


def plan(world: World, child: Entity, helper: Entity, snack: Snack) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} wanted to make an appetizing surprise for {helper.id}. "
        f'{child.id} whispered, "Don\'t peek yet!" and started stacking '
        f'{snack.phrase}.'
    )


def mixup(world: World, child: Entity, snack: Snack) -> None:
    child.memes["worry"] += 1
    world.say(
        f"Then {child.id} made a silly mistake: {snack.secret} tipped into the bowl, "
        f"and for one second the whole plan looked very strange."
    )


def save(world: World, helper: Entity, response: Response, snack: Snack) -> None:
    snack_ent = world.get("snack")
    snack_ent.meters["messy"] = 0.0
    body = response.text.replace("{snack}", snack.label)
    world.say(
        f"{helper.label_word.capitalize()} came over, laughed, and {body}."
    )
    world.say(
        f"The surprise was still appetizing, just a little more lopsided than planned."
    )


def fail_save(world: World, helper: Entity, response: Response, snack: Snack) -> None:
    snack_ent = world.get("snack")
    snack_ent.meters["messy"] += 1
    body = response.fail.replace("{snack}", snack.label)
    world.say(f"{helper.label_word.capitalize()} tried to help, but {body}.")
    world.say("The snack looked funny and the room got a bit too chaotic.")


def reveal(world: World, child: Entity, helper: Entity, snack: Snack) -> None:
    child.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    world.say(
        f"At last, {child.id} lifted the cover. Under it was {snack.phrase}, "
        f"and the little surprise made {helper.id} grin."
    )
    world.say(
        f"They both laughed because the snack was appetizing and the secret was "
        f"actually a smile-shaped one."
    )


def tell(scene: "Scene", snack: Snack, response: Response,
         child_name: str = "Mila", child_gender: str = "girl",
         helper_name: str = "Dad", helper_gender: str = "father") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    kitchen = world.add(Entity(id="kitchen", type="room", label="the kitchen"))
    snack_ent = world.add(Entity(id="snack", type="thing", label=snack.label))
    snack_ent.meters["fresh"] = 1.0
    snack_ent.meters["hidden"] = 1.0

    world.say(
        f"On a quiet afternoon, {child.id} and {helper.id} worked in the kitchen. "
        f"The room felt bright, and the counter was ready for a joke."
    )
    smell(world, snack, child)
    plan(world, child, helper, snack)

    world.para()
    child.memes["surprise"] += 1
    world.say(
        f"{child.id} was trying to keep the secret hidden, but the secret wanted "
        f"to be funny too."
    )
    mixup(world, child, snack)
    _do_sneaky(world, snack_ent, narrate=False)

    contained = response.rescue >= 2
    world.para()
    if contained:
        save(world, helper, response, snack)
    else:
        fail_save(world, helper, response, snack)

    world.para()
    reveal(world, child, helper, snack)
    world.say(
        f"In the end, the surprise stayed appetizing, the joke landed, and the "
        f"kitchen smelled like a tiny celebration."
    )

    world.facts.update(
        scene=scene,
        snack=snack,
        response=response,
        child=child,
        helper=helper,
        kitchen=kitchen,
        contained=contained,
        warned=True,
    )
    return world


@dataclass
class Scene:
    id: str
    place: str
    mood: str
    setup: str
    ending: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SCENES = {
    "kitchen": Scene("kitchen", "the kitchen", "bright", "the counter was ready for a joke", "like a tiny celebration"),
    "picnic": Scene("picnic", "the picnic blanket", "sunny", "the basket was waiting under a tree", "like a cheerful picnic"),
    "bakery": Scene("bakery", "the little bakery", "busy", "the tray was lined up in a row", "like a sweet parade"),
}

SNACKS = {
    "fruit_cups": Snack("fruit_cups", "fruity", "a bowl of fruit cups", True, "sweet", "a grape rolled away", {"fruit"}),
    "toast_smile": Snack("toast_smile", "toasty", "a plate of smiley toast", True, "savory", "the butter made a face", {"toast"}),
    "cookie_stack": Snack("cookie_stack", "cookie-good", "a tower of cookies", True, "sweet", "one cookie wore powdered sugar like a hat", {"cookie"}),
}

RESPONSES = {
    "napkin_cover": Response(
        "napkin_cover", 3, 3,
        "slid a napkin over the bowl and saved the surprise with a grin",
        "slid a napkin over the bowl, but the mess had already taken over",
        "slid a napkin over the bowl and saved the surprise",
        {"cover", "cleanup"},
    ),
    "tray_flip": Response(
        "tray_flip", 2, 2,
        "turned the tray around so the lopsided side faced the wall and nobody noticed",
        "turned the tray around, but it wobbled and made the joke even bigger",
        "turned the tray around and hid the wobble",
        {"tray", "cleanup"},
    ),
    "spoon_stir": Response(
        "spoon_stir", 2, 2,
        "gave the bowl three quick stirs and made the whole thing look deliberately silly",
        "gave the bowl three quick stirs, but it still looked like a disaster",
        "gave the bowl three quick stirs and made it look silly on purpose",
        {"spoon", "cleanup"},
    ),
    "paper_towel": Response(
        "paper_towel", 1, 1,
        "wiped with a paper towel and hoped the joke would behave itself",
        "wiped with a paper towel, but the spill was too stubborn",
        "wiped with a paper towel",
        {"cleanup"},
    ),
}


@dataclass
@dataclass
class StoryParams:
    scene: str
    snack: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def explain_rejection(snack: Snack, response: Response) -> str:
    if response.sense < SENSE_MIN:
        return f"(No story: the response {response.id} is too weak for a comic rescue.)"
    return f"(No story: {snack.label} is not appetizing enough for this surprise comedy.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Appetizing surprise comedy storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.snack and args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_rejection(SNACKS[args.snack], RESPONSES[args.response]))
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.snack is None or c[1] == args.snack)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, snack_id, response = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(["Mila", "Nina", "Ari", "Luca", "Zoe", "Ivy", "Ben", "Max"])
    helper_gender = rng.choice(["mother", "father"])
    helper_name = args.helper or rng.choice(["Mom", "Dad"])
    return StoryParams(scene, snack_id, response, child_name, child_gender, helper_name, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    snack = f["snack"]
    scene = f["scene"]
    return [
        f'Write a funny story for a small child that includes the word "appetizing" and takes place at {scene.place}.',
        f"Tell a comedy about {f['child'].id} making an appetizing surprise with {snack.phrase} and trying not to spoil it.",
        f"Write a gentle surprise story where a child keeps a tasty secret, then the family laughs when the reveal happens.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    snack = f["snack"]
    scene = f["scene"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id} working together in {scene.place}. The child is the one planning the surprise."),
        ("What made the snack important?",
         f"The snack was meant to be appetizing, so the surprise would taste nice and make everyone smile. That is why the secret had to stay hidden for a while."),
    ]
    if f["contained"]:
        qa.append((
            "How did the helper deal with the mistake?",
            f"{helper.id} laughed and used a quick cleanup move so the surprise could stay fun. The mix-up got smaller instead of ruining {snack.label}."
        ))
    qa.append((
        "How did the story end?",
        f"The surprise was revealed and everyone laughed. The ending image is a kitchen that smells like a tiny celebration, which proves the plan worked."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    snack = world.facts["snack"]
    tags = set(snack.tags)
    out = []
    if "fruit" in tags:
        out.append(("Why do fruit cups smell good?",
                    "Fruit cups smell good because fruit is sweet and fresh. The smell can make a snack feel appetizing before you even taste it."))
    if "toast" in tags:
        out.append(("Why can toast be funny in a story?",
                    "Toast can be funny because it is ordinary, and a silly shape or smile on it can make people laugh. Simple food makes good comedy."))
    if "cookie" in tags:
        out.append(("Why do cookies feel like a surprise treat?",
                    "Cookies often feel like a surprise treat because they are sweet and small. A little tower of cookies can look extra cheerful."))
    out.append(("What does appetizing mean?",
                "Appetizing means food looks or smells so good that it makes you want to eat it right away. It is a word for tasty, tempting food."))
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
    for e in list(world.entities.values()):
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "fruit_cups", "napkin_cover", "Mila", "girl", "Dad", "father"),
    StoryParams("picnic", "cookie_stack", "tray_flip", "Ben", "boy", "Mom", "mother"),
    StoryParams("bakery", "toast_smile", "spoon_stir", "Ari", "girl", "Dad", "father"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        if snack.appetizing:
            lines.append(asp.fact("appetizing", snack_id))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("rescue", rid, r.rescue))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(Scene, Snack, Resp) :- scene(Scene), snack(Snack), appetizing(Snack), sensible(Resp).
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
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        p = CURATED[0]
        sample = generate(p)
        _ = sample.story
        _ = sample.to_json()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], SNACKS[params.snack], RESPONSES[params.response],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print()
        for scene, snack, resp in asp_valid_combos():
            print(f"{scene:8} {snack:12} {resp}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.child_name}: {p.snack} at {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
