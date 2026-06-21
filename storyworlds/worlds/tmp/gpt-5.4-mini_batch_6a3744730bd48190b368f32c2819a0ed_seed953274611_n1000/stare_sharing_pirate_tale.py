#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stare_sharing_pirate_tale.py
=============================================================

A tiny storyworld for a pirate-style sharing tale: one child stares at a prized
treasure, another child worries, and a grown-up guides them toward sharing so
the crew stays happy. The world is small on purpose: a handful of pirates, a
single coveted object, a simple tension, and a sharing turn that changes the
ending image.

The story engine is state-driven. Characters have physical meters and emotional
memes; events change those values, and the renderer turns the resulting state
into prose. The target word "stare" appears naturally in the stories, and the
central feature is sharing.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
    shared: bool = False
    edible: bool = False

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
class Setting:
    id: str
    place: str
    scene: str
    ship_name: str
    dark_spot: str
    title: str = "pirates"


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    gleam: str
    shareable: bool = True
    tied_to: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    cheer: str
    shareable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    snack = world.entities.get("snack")
    if not snack or snack.shared:
        return out
    if snack.meters["wanted"] < THRESHOLD:
        return out
    sig = ("share", snack.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    snack.shared = True
    for kid in world.characters():
        kid.memes["joy"] += 1
    out.append("__shared__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.memes["want"] >= THRESHOLD and kid.meters.get("received", 0) >= THRESHOLD:
            sig = ("settle", kid.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            kid.memes["calm"] += 1
            out.append(f"{kid.id} smiled.")
    return out


CAUSAL_RULES = [Rule("share", _r_share), Rule("settle", _r_settle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, t in TREASURES.items():
            for cid, c in COMFORTS.items():
                if t.shareable and c.shareable:
                    combos.append((sid, tid, cid))
    return combos


def predict_share(world: World, target_id: str) -> dict:
    sim = world.copy()
    sim.get(target_id).meters["wanted"] += 1
    propagate(sim, narrate=False)
    return {"shared": sim.get(target_id).shared}


def _stare(world: World, child: Entity, treasure: Treasure) -> None:
    child.meters["staring"] += 1
    child.memes["want"] += 1
    world.say(
        f"{child.id} gave the {treasure.label} a long stare. "
        f"It gleamed like a coin in moonlight, and {child.pronoun('possessive')} eyes would not leave it."
    )


def _warn(world: World, helper: Entity, child: Entity, treasure: Treasure) -> None:
    pred = predict_share(world, "snack")
    if pred["shared"]:
        world.facts["pred_shared"] = True
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} noticed the stare and spoke softly. "
        f'"If we keep it all to ourselves, the crew feels left out. Can we share {treasure.phrase} instead?"'
    )


def _refuse(world: World, child: Entity) -> None:
    child.memes["grumpy"] += 1
    world.say(f'"No," {child.id} said, hugging the snack close like a secret map."')


def _share(world: World, helper: Entity, child: Entity, snack: Comfort) -> None:
    snack_ent = world.get("snack")
    snack_ent.meters["wanted"] = 0.0
    snack_ent.shared = True
    world.get(child.id).meters["received"] += 1
    world.get(helper.id).meters["received"] += 1
    helper.memes["joy"] += 1
    child.memes["joy"] += 1
    child.memes["grumpy"] = 0.0
    world.say(
        f"{helper.id} broke the treat in two and passed half to {child.id}. "
        f"Together they shared {snack.phrase}, and the little pirate ship felt bigger than before."
    )


def _ending(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"After that, {child.id} and {helper.id} sat on the deck with crumbs on their fingers, "
        f"grinning at the same shiny plate, the kind of quiet pirate smile that comes after a fair share."
    )


def tell(setting: Setting, treasure: Treasure, comfort: Comfort,
         child_name: str = "Pip", child_gender: str = "boy",
         helper_name: str = "Luna", helper_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    ship = world.add(Entity(id="ship", type="thing", label=setting.ship_name))
    snack = world.add(Entity(id="snack", type="thing", label=comfort.label))
    snack.meters["wanted"] = 1.0

    world.say(
        f"On the {setting.place}, the crew turned the deck into {setting.scene}. "
        f"The {setting.ship_name} rocked softly, and a small stash of {treasure.phrase} waited nearby."
    )
    world.say(
        f"{child.id} and {helper.id} were playing pirates when they found {treasure.phrase}. "
        f"{treasure.gleam}"
    )

    world.para()
    _stare(world, child, treasure)
    _warn(world, helper, child, treasure)

    if child_name == helper_name:
        raise StoryError("Child and helper must be different characters.")

    world.para()
    if treasure.tied_to and treasure.tied_to != setting.id:
        raise StoryError("Treasure does not fit this setting.")
    _refuse(world, child)
    if treasure.shareable:
        _share(world, helper, child, comfort)
        _ending(world, child, helper)

    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        treasure=treasure,
        comfort=comfort,
        setting=setting,
        shared=snack.shared,
        ship=ship,
    )
    return world


SETTINGS = {
    "harbor": Setting(
        id="harbor",
        place="the harbor",
        scene="a pirate camp with ropes, shells, and a map",
        ship_name="little ship",
        dark_spot="under the sail",
    ),
    "island": Setting(
        id="island",
        place="the island",
        scene="a pirate fort with driftwood, a flag, and a drum",
        ship_name="tiny raft",
        dark_spot="behind the treasure chest",
    ),
    "cove": Setting(
        id="cove",
        place="the cove",
        scene="a sandy hideout with lanterns, buckets, and a lookout rock",
        ship_name="brave skiff",
        dark_spot="inside the cave mouth",
    ),
}

TREASURES = {
    "shell": Treasure(
        id="shell",
        label="shell necklace",
        phrase="a shell necklace",
        gleam="It shone pearly and bright, like the sea had tied up a small star.",
        tied_to="harbor",
        tags={"shell"},
    ),
    "map": Treasure(
        id="map",
        label="map scrap",
        phrase="a treasure map scrap",
        gleam="It rustled like a secret and showed a tiny X in the corner.",
        tied_to="island",
        tags={"map"},
    ),
    "coin": Treasure(
        id="coin",
        label="gold coin",
        phrase="a gold coin",
        gleam="It flashed like a tiny sunrise, warm and round in the sand.",
        tied_to="cove",
        tags={"coin"},
    ),
}

COMFORTS = {
    "cracker": Comfort(
        id="cracker",
        label="cracker pieces",
        phrase="cracker pieces",
        cheer="They crunched like tiny sails snapping in the wind.",
        tags={"sharing"},
    ),
    "apple": Comfort(
        id="apple",
        label="apple slices",
        phrase="apple slices",
        cheer="They were sweet and crisp, red as a flag at sunset.",
        tags={"sharing"},
    ),
    "fishcake": Comfort(
        id="fishcake",
        label="fishcake bites",
        phrase="fishcake bites",
        cheer="They smelled warm and cozy, like supper on a brave night.",
        tags={"sharing"},
    ),
}

RESPONSES = {
    "share": Response(
        id="share",
        sense=3,
        power=3,
        text="shared the snack and made sure everyone had a piece",
        fail="tried to share, but the snack was already gone",
        tags={"sharing"},
    ),
    "cut": Response(
        id="cut",
        sense=3,
        power=2,
        text="cut the snack into even pieces and passed them around",
        fail="cut too slowly and the pirates got impatient",
        tags={"sharing"},
    ),
    "save": Response(
        id="save",
        sense=1,
        power=1,
        text="hid the snack under the mast",
        fail="hid it too well and nobody got a taste",
        tags={"greedy"},
    ),
}

SENSE_MIN = 2

GIRL_NAMES = ["Luna", "Mira", "Nia", "Ivy", "Tessa"]
BOY_NAMES = ["Pip", "Finn", "Ned", "Toby", "Jules"]
PARENT_NAMES = ["mother", "father"]


@dataclass
class StoryParams:
    setting: str
    treasure: str
    comfort: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    response: str = "share"
    seed: Optional[int] = None


KNOWLEDGE = {
    "sharing": [
        ("What is sharing?",
         "Sharing means letting other people use or enjoy something with you. It helps friends feel included."),
        ("Why do pirates share treasure?",
         "Pirates share treasure so everyone on the crew gets a fair turn. That keeps the crew happy and working together."),
    ],
    "stare": [
        ("What does it mean to stare?",
         "To stare means to look at something for a long time without looking away. It often shows strong interest or surprise."),
    ],
    "pirate": [
        ("What is a pirate crew?",
         "A pirate crew is a group of people who sail together on a ship and help each other."),
    ],
}
KNOWLEDGE_ORDER = ["pirate", "stare", "sharing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the word "stare" and ends with sharing.',
        f"Tell a small pirate story where {f['child'].id} stares at {f['treasure'].phrase}, then learns to share with {f['helper'].id}.",
        f"Write a gentle pirate story about a crew, a treasure, and a fair share.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    treasure = f["treasure"]
    comfort = f["comfort"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {helper.id}, and their pirate crew on the {f['setting'].place}."),
        ("What did {0} do when the treasure was found?".format(child.id),
         f"{child.id} gave the {treasure.label} a long stare, because {treasure.phrase} looked so special."),
        ("How did the story end?",
         f"It ended with sharing. {helper.id} broke up {comfort.phrase} and gave {child.id} a piece, so they could enjoy it together."),
    ]
    if f.get("shared"):
        qa.append((
            "Why was sharing important?",
            f"Sharing made the pirate crew feel fair and happy. It turned one tempting treat into a friendly moment for everyone."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["treasure"].tags) | set(world.facts["comfort"].tags) | {"sharing", "stare", "pirate"}
    out: list[tuple[str, str]] = []
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="harbor",
        treasure="shell",
        comfort="cracker",
        child="Pip",
        child_gender="boy",
        helper="Luna",
        helper_gender="girl",
        parent="mother",
        response="share",
    ),
    StoryParams(
        setting="island",
        treasure="map",
        comfort="apple",
        child="Mira",
        child_gender="girl",
        helper="Ned",
        helper_gender="boy",
        parent="father",
        response="cut",
    ),
    StoryParams(
        setting="cove",
        treasure="coin",
        comfort="fishcake",
        child="Toby",
        child_gender="boy",
        helper="Ivy",
        helper_gender="girl",
        parent="mother",
        response="share",
    ),
]


def explain_rejection(response: Response) -> str:
    return f"(Refusing response '{response.id}': it is not sensible enough for a fair sharing story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld about staring and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_rejection(RESPONSES[args.response]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.treasure is None or c[1] == args.treasure)
              and (args.comfort is None or c[2] == args.comfort)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treasure, comfort = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES + BOY_NAMES) if n != child]
    helper = args.helper or rng.choice(helper_pool)
    parent = args.parent or rng.choice(PARENT_NAMES)
    response = args.response or "share"
    return StoryParams(
        setting=setting,
        treasure=treasure,
        comfort=comfort,
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        response=response,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.treasure not in TREASURES:
        raise StoryError("Unknown treasure.")
    if params.comfort not in COMFORTS:
        raise StoryError("Unknown sharing item.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    world = tell(
        SETTINGS[params.setting],
        TREASURES[params.treasure],
        COMFORTS[params.comfort],
        child_name=params.child,
        child_gender=params.child_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
wanted(S) :- sailor(S).
shareable(T) :- treasure(T).
shared :- wanted(snack), shareable(snack).
outcome(shared) :- shared.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("shareable", tid))
    for cid in COMFORTS:
        lines.append(asp.fact("snack", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    ok = bool(asp.atoms(model, "outcome"))
    if ok:
        print("OK: ASP twin produced an outcome.")
    else:
        print("MISMATCH: ASP twin did not produce an outcome.")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for this tiny world.")
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
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            params.seed = seed
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
            header = f"### {p.child} and {p.helper} at {p.setting} ({p.treasure}, share)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
