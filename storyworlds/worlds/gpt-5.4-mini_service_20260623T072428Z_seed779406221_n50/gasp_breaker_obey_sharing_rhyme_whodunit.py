#!/usr/bin/env python3
"""
storyworlds/worlds/gasp_breaker_obey_sharing_rhyme_whodunit.py
===============================================================

A small whodunit storyworld about a missing/shared object, a surprised gasp,
a breaker of a rule, and a child who chooses to obey.

Premise:
- A child story in a cozy place.
- One valued object goes missing or is mishandled.
- The search unfolds through clues, sharing, and a rhyme.
- The ending reveals who did it, why, and how obeying fixed the trouble.

The story keeps a whodunit feel: clues, suspicion, careful questioning, a
reveal, and a final repair. The generated prose is driven by state, not by a
frozen paragraph template.

Seed words required by the request:
- gasp
- breaker
- obey
- Sharing
- Rhyme
- Whodunit style
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    giver: Optional[str] = None
    receiver: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = True
    afford_share: bool = True
    afford_rhyme: bool = True


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    owner_role: str
    shareable: bool = True
    plural: bool = False
    kind: str = "thing"


@dataclass
class Clue:
    id: str
    line: str
    tells: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Breaker:
    id: str
    label: str
    act: str
    clue: str
    mess: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.entities.get("breaker")
    item = world.entities.get("sharing_item")
    if not culprit or not item:
        return out
    if culprit.meters["spill"] < THRESHOLD:
        return out
    sig = ("spill", culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["messy"] += 1
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["alarm"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill)]


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


def sharing_possible(item: ObjectThing) -> bool:
    return item.shareable


def clue_rhyme() -> str:
    return "When the bell goes ding, the missing thing will sing."


def predict_spill(world: World) -> bool:
    sim = world.copy()
    simulate_break(sim, narrate=False)
    return sim.get("sharing_item").meters["messy"] >= THRESHOLD


def simulate_break(world: World, narrate: bool = True) -> None:
    breaker = world.get("breaker")
    item = world.get("sharing_item")
    breaker.meters["spill"] += 1
    breaker.memes["gasp"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"{breaker.id} reached for the {item.label}, but {breaker.label_word} "
            f"had already tipped it."
        )


def setup_scene(world: World, detective: Entity, friend: Entity, setting: Setting, item: ObjectThing) -> None:
    detective.memes["curious"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"At {setting.place}, {detective.id} and {friend.id} were sharing a quiet day."
    )
    world.say(
        f"They had a {item.phrase} on the table, and everyone knew it was meant to be shared."
    )


def first_gasp(world: World, breaker: Entity, item: ObjectThing) -> None:
    breaker.memes["gasp"] += 1
    world.say(
        f"Then came a gasp. {breaker.id} had seen the {item.label} wobble near the edge."
    )
    world.say(
        f"{breaker.id} moved too fast and tried to grab it before anyone else could obey the rule to wait."
    )


def clue_scene(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["solve"] += 1
    world.say(
        f"{detective.id} noticed a clue: {clue.line}"
    )
    world.say(
        f"It pointed to {clue.tells}, and the little mystery felt clearer."
    )


def suspect_scene(world: World, detective: Entity, suspect: Entity, item: ObjectThing) -> None:
    world.say(
        f"{detective.id} asked {suspect.id} a careful question about the {item.label}."
    )
    if suspect.id == "breaker":
        world.say(
            f"{suspect.id} looked down at once, because {suspect.pronoun()} knew the spill had happened."
        )
    else:
        world.say(
            f"{suspect.id} shook {suspect.pronoun()} head; {suspect.pronoun()} had only been sharing the table."
        )


def reveal(world: World, detective: Entity, breaker: Entity, item: ObjectThing, clue: Clue) -> None:
    world.say(
        f"At last, {detective.id} put the pieces together."
    )
    world.say(
        f"The one who broke the calm was {breaker.id}: {breaker.act}. {clue.tells}."
    )
    world.say(
        f"The rhyme made the answer easy to hear: “{clue_rhyme()}”"
    )


def obey_and_fix(world: World, detective: Entity, breaker: Entity, item: ObjectThing) -> None:
    breaker.memes["gasp"] += 1
    breaker.memes["regret"] += 1
    breaker.memes["obey"] += 1
    breaker.meters["spill"] = 0.0
    item.meters["messy"] = 0.0
    world.say(
        f"{breaker.id} stopped, took a breath, and chose to obey."
    )
    world.say(
        f"Together they wiped the {item.label}, shared the job, and set it back where it belonged."
    )
    world.say(
        f"By the end, the room was calm again, and {detective.id} could smile at the tidy table."
    )


def tell(setting: Setting, item_cfg: ObjectThing, clue: Clue, breaker_cfg: Breaker,
         detective_name: str = "Mina", detective_type: str = "girl",
         friend_name: str = "Owen", friend_type: str = "boy") -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, role="detective"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    breaker = world.add(Entity(id="breaker", kind="character", type=friend_type, role="breaker", label=breaker_cfg.label))
    sharing_item = world.add(Entity(id="sharing_item", kind="thing", type=item_cfg.id, label=item_cfg.label))
    world.facts["item_cfg"] = item_cfg
    world.facts["clue"] = clue
    world.facts["breaker_cfg"] = breaker_cfg
    world.facts["detective"] = detective
    world.facts["friend"] = friend
    world.facts["breaker"] = breaker
    world.facts["sharing_item"] = sharing_item

    setup_scene(world, detective, friend, setting, item_cfg)
    world.para()
    first_gasp(world, breaker, item_cfg)
    clue_scene(world, detective, clue)
    world.para()
    suspect_scene(world, detective, friend, item_cfg)
    suspect_scene(world, detective, breaker, item_cfg)
    world.para()
    reveal(world, detective, breaker, item_cfg, clue)
    obey_and_fix(world, detective, breaker, item_cfg)

    world.facts["resolved"] = True
    world.facts["gasped"] = breaker.memes["gasp"] >= THRESHOLD
    world.facts["obeyed"] = breaker.memes["obey"] >= THRESHOLD
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen"),
    "classroom": Setting(place="the classroom"),
    "library": Setting(place="the library"),
}

ITEMS = {
    "cake": ObjectThing(id="cake", label="cake", phrase="a small cake", owner_role="shared"),
    "crayons": ObjectThing(id="crayons", label="box of crayons", phrase="a box of crayons", owner_role="shared", plural=True),
    "book": ObjectThing(id="book", label="book", phrase="a picture book", owner_role="shared"),
}

CLUES = {
    "crumbs": Clue(id="crumbs", line="there were crumbs on the blue chair", tells="the cake had moved from the tray to the chair", tags={"cake"}),
    "page": Clue(id="page", line="a page was open to the rhyming verse", tells="the book had been left open to the shared rhyme", tags={"book", "rhyme"}),
    "stripe": Clue(id="stripe", line="there was a red stripe on the tablecloth", tells="the crayons had rolled across the table", tags={"crayons"}),
}

BREAKERS = {
    "hasty": Breaker(id="hasty", label="the hasty one", act="moved too fast", clue="gasp", mess="spill", tags={"gasp"}),
    "breaker": Breaker(id="breaker", label="the breaker", act="broke the rule to wait", clue="breaker", mess="spill", tags={"breaker"}),
    "mischief": Breaker(id="mischief", label="the little rule-breaker", act="reached before asking", clue="obey", mess="spill", tags={"obey"}),
}

GIRL_NAMES = ["Mina", "Tess", "Nora", "Lila", "June", "Ivy"]
BOY_NAMES = ["Owen", "Eli", "Finn", "Theo", "Noah", "Ben"]


@dataclass
class StoryParams:
    setting: str
    item: str
    clue: str
    breaker: str
    detective_name: str
    detective_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in ITEMS:
            for c in CLUES:
                combos.append((s, i, c))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit in {f["item_cfg"].label} time, with a gasp, a breaker, and a child who learns to obey.',
        f"Tell a mystery story in {f['detective'].id}'s world where sharing gets interrupted, a rhyme gives the clue, and the ending is calm.",
        f'Write a short whodunit with the word "{f["breaker_cfg"].label}" and a rhyme clue that helps solve a small sharing problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    breaker = f["breaker"]
    item = f["item_cfg"]
    clue = f["clue"]
    return [
        QAItem(
            question=f"Who was the story about at {world.setting.place}?",
            answer=f"It was about {detective.id}, {breaker.id}, and a sharing problem around {item.label}.",
        ),
        QAItem(
            question=f"What made everyone gasp?",
            answer=f"The gasp came when {breaker.id} moved too fast and tipped the {item.label}.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The clue was that {clue.line}, which showed what had happened to the {item.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended with the breaker choosing to obey, helping clean up, and sharing the work until the room was calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use, hold, or enjoy something together instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little word sound pattern, like when the ends of words sound alike.",
        ),
        QAItem(
            question="What does obey mean?",
            answer="To obey means to listen and do what the rule or grown-up says.",
        ),
    ]
    if f["item_cfg"].label == "cake":
        out.append(QAItem(question="Why can cake be tricky to share?", answer="Cake is soft and crumbly, so it can fall apart if someone grabs it too fast."))
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "cake", "crumbs", "breaker", "Mina", "girl", "Owen", "boy"),
    StoryParams("classroom", "crayons", "stripe", "hasty", "Tess", "girl", "Finn", "boy"),
    StoryParams("library", "book", "page", "mischief", "Nora", "girl", "Theo", "boy"),
]


def explain_rejection(setting: Setting, item: ObjectThing) -> str:
    if not sharing_possible(item):
        return "(No story: this object cannot be shared in a believable way.)"
    return f"(No story: {item.label} does not fit this whodunit setup at {setting.place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with sharing, rhyme, gasp, breaker, and obey.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--breaker", choices=BREAKERS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, clue = rng.choice(sorted(combos))
    breaker = args.breaker or rng.choice(sorted(BREAKERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    detective_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    return StoryParams(setting, item, clue, breaker, detective_name, gender, friend_name, friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], CLUES[params.clue], BREAKERS[params.breaker],
                 params.detective_name, params.detective_type, params.friend_name, params.friend_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
shareable(I) :- item(I), shareable_item(I).
mystery(S, I, C) :- setting(S), item(I), clue(C).
breaker(B) :- breaker_id(B).
gasped(B) :- breaker(B), spill(B).
obeyed(B) :- breaker(B), obey(B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.shareable:
            lines.append(asp.fact("shareable_item", iid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for bid in BREAKERS:
        lines.append(asp.fact("breaker_id", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shareable/1.\n#show mystery/3."))
    # Minimal parity check: generated facts exist and are solvable.
    if model is not None:
        print("OK: ASP model solved.")
        return 0
    print("MISMATCH: ASP returned no model.")
    return 1


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
        print(asp_program("#show shareable/1.\n#show mystery/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show mystery/3."))
        print(asp.atoms(model, "mystery"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.detective_name}: {p.item} at {p.setting} ({p.breaker})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
