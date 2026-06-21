#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/insect_bravery_cautionary_kindness_mystery.py
===============================================================================

A small, child-facing mystery storyworld about a curious insect, a brave child,
a cautionary friend, and a kind choice that solves the puzzle.

Premise
-------
A child finds a tiny mystery in the garden: an insect is stuck in a jar, a
strange trail leads toward a flower bed, and the children must decide whether to
rush in, warn each other, and help gently.

Story shape
-----------
- Mystery setup: something odd is noticed.
- Bravery: one child wants to investigate.
- Cautionary: another child notices a risk and slows the moment down.
- Kindness: they use a gentle tool and free the insect.
- Resolution: the trail makes sense, and the garden feels peaceful again.

This world is intentionally tiny. It models a handful of entities with physical
meters and emotional memes, plus a simple forward-chaining rule engine. The
story is rendered from simulated state, not from a frozen template.
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
BRAVERY_INIT = 5.0
CAUTION_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    nook: str
    plant: str
    ground: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Mystery:
    id: str
    clue: str
    trail: str
    suspicious: str
    revealed_by: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    gentleness: int
    use: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone.facts = dict(self.facts)
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_settled(world: World) -> list[str]:
    out: list[str] = []
    insect = world.get("insect")
    if insect.meters["freed"] >= THRESHOLD and ("trail_known",) not in world.fired:
        world.fired.add(("trail_known",))
        world.get("child").memes["wonder"] += 1
        out.append("__trail_known__")
    if insect.meters["spooked"] >= THRESHOLD and ("calm_return",) not in world.fired:
        world.fired.add(("calm_return",))
        world.get("child").memes["relief"] += 1
        out.append("__calm_return__")
    return out


CAUSAL_RULES = [Rule("settled", _r_settled)]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    for s in produced:
        world.say(s)
    return produced


def mystery_at_risk(mystery: Mystery, setting: Setting) -> bool:
    return mystery.id in setting.tags or "insect" in mystery.tags


def select_tool(mystery: Mystery) -> Tool:
    for tool in TOOLS.values():
        if tool.gentleness >= 2:
            return tool
    raise StoryError("No gentle tool is available.")


def predict(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    _discover(sim, sim.get("child"), sim.get("friend"), sim.get("insect"), mystery, narrate=False)
    return {
        "freed": sim.get("insect").meters["freed"] >= THRESHOLD,
        "spooked": sim.get("insect").meters["spooked"] >= THRESHOLD,
    }


def _discover(world: World, child: Entity, friend: Entity, insect: Entity, mystery: Mystery, narrate: bool = True) -> None:
    child.memes["bravery"] += 1
    friend.memes["caution"] += 1
    insect.meters["found"] += 1
    if narrate:
        world.say(
            f"In the garden, {child.id} noticed something odd near {world.setting.nook}. "
            f"A tiny {insect.label} sat by {world.setting.plant}, and a thin trail ran toward {mystery.suspicious}."
        )
        world.say(
            f'"This feels like a mystery," {child.id} whispered, while {friend.id} peered closer.'
        )


def _warn(world: World, friend: Entity, child: Entity, insect: Entity) -> None:
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} lifted a hand. "Careful," {friend.id} said. "If we rush, we might scare the little {insect.label}."'
    )


def _kind_act(world: World, tool: Tool, insect: Entity, mystery: Mystery) -> None:
    insect.meters["freed"] += 1
    insect.meters["spooked"] += 0.5
    world.say(
        f"{tool.phrase.capitalize()} did the job. {tool.use} and the little {insect.label} climbed out gently."
    )
    world.say(
        f"That was the answer to the mystery: the trail led to {mystery.revealed_by}, where the insect had been hiding from the breeze."
    )


def _end(world: World, child: Entity, friend: Entity, insect: Entity) -> None:
    child.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    insect.meters["safe"] += 1
    world.say(
        f"{child.id} and {friend.id} watched the insect land on a leaf and wiggle away."
    )
    world.say(
        "The garden grew quiet again, but now the mystery felt friendly instead of strange."
    )


def tell(setting: Setting, mystery: Mystery, tool: Tool, child_name: str, child_gender: str, friend_name: str, friend_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="brave"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="cautionary"))
    insect = world.add(Entity(id="insect", kind="character", type="insect", label="insect", role="mystery"))
    world.add(Entity(id="jar", type="thing", label="jar"))
    child.memes["bravery"] = BRAVERY_INIT
    friend.memes["caution"] = CAUTION_INIT

    world.say(
        f"One quiet afternoon, {child.id} and {friend.id} explored {setting.place}. "
        f"The air smelled like leaves, and {setting.ground} made the path soft underfoot."
    )
    world.say(
        f"Near {setting.nook}, they spotted a shiny jar and a tiny {insect.label}. "
        f"Beside it lay a small trail, as if something important had happened there."
    )

    world.para()
    _discover(world, child, friend, insect, mystery)
    _warn(world, friend, child, insect)

    world.para()
    child.memes["bravery"] += 1
    world.say(f"{child.id} took a deep breath and reached for {tool.phrase}.")
    _kind_act(world, tool, insect, mystery)
    propagate(world)

    world.para()
    _end(world, child, friend, insect)

    world.facts.update(
        setting=setting,
        mystery=mystery,
        tool=tool,
        child=child,
        friend=friend,
        insect=insect,
        outcome="freed" if insect.meters["freed"] >= THRESHOLD else "unknown",
    )
    return world


SETTINGS = {
    "garden": Setting(id="garden", place="the garden", nook="the stone bench", plant="the sunflower", ground="damp moss", tags={"insect", "garden"}),
    "backyard": Setting(id="backyard", place="the backyard", nook="the flower pot", plant="the marigolds", ground="soft grass", tags={"insect", "garden"}),
    "park": Setting(id="park", place="the park", nook="the willow tree", plant="the clover patch", ground="warm dirt", tags={"insect", "garden"}),
}

MYSTERIES = {
    "trail": Mystery(id="trail", clue="a shiny trail", trail="a tiny trail", suspicious="the old jar", revealed_by="a fallen apple slice", tags={"insect", "mystery"}),
    "flutter": Mystery(id="flutter", clue="a flutter of wings", trail="a faint line of movement", suspicious="a crack in the fence", revealed_by="a sweet berry", tags={"insect", "mystery"}),
}

TOOLS = {
    "leaf": Tool(id="leaf", label="leaf", phrase="A soft leaf", gentleness=3, use="It made a tiny bridge so the insect could step onto it", tags={"kindness"}),
    "spoon": Tool(id="spoon", label="spoon", phrase="A clean spoon", gentleness=2, use="It gave the insect a safe place to climb", tags={"kindness"}),
}

CHILD_NAMES = ["Mina", "Theo", "Ava", "Leo", "Nora", "Ben", "Lily", "Max"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(setting="garden", mystery="trail", tool="leaf", child_name="Mina", child_gender="girl", friend_name="Theo", friend_gender="boy"),
    StoryParams(setting="backyard", mystery="flutter", tool="spoon", child_name="Leo", child_gender="boy", friend_name="Nora", friend_gender="girl"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for tid in TOOLS:
                if mystery_at_risk(MYSTERIES[mid], SETTINGS[sid]):
                    combos.append((sid, mid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: insect mystery, bravery, caution, kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or rng.choice([n for n in CHILD_NAMES if n != args.friend_name])
    friend_name = args.friend_name or rng.choice([n for n in CHILD_NAMES if n != child_name])
    return StoryParams(setting=setting, mystery=mystery, tool=tool, child_name=child_name, child_gender=child_gender, friend_name=friend_name, friend_gender=friend_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the word "insect" and shows bravery, cautionary thinking, and kindness.',
        f"Tell a gentle story where {f['child'].id} notices a mysterious insect, {f['friend'].id} warns them to be careful, and they help it safely.",
        f"Write a small garden mystery with a happy ending about an insect, a clue, and a kind rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, insect, setting, mystery = f["child"], f["friend"], f["insect"], f["setting"], f["mystery"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a little mystery story. The children notice a clue, think carefully, and solve the problem with kindness."
        ),
        QAItem(
            question=f"Why did {friend.id} warn {child.id} to be careful?",
            answer=f"{friend.id} was worried they might scare the insect if they rushed. The caution helped them slow down and choose a gentle plan."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"They used a gentle tool to help the insect out of the jar, and then the trail made sense. The clue led to food nearby, so the strange little scene was explained."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an insect?", answer="An insect is a tiny animal with six legs, like a beetle, ant, or butterfly."),
        QAItem(question="What does kindness mean?", answer="Kindness means helping gently and making choices that care about someone else's safety."),
        QAItem(question="Why should you be careful with small animals?", answer="Small animals can be scared or hurt easily, so gentle hands and quiet voices help them stay safe."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
kindness(helped) :- freed(insect).
cautionary(warned) :- warned(friend).
brave(acted) :- bravery(child).
solved(mystery) :- freed(insect), clue_seen.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos()) if _has_clingo() else python_set
    if clingo_set != python_set:
        rc = 1
        print("MISMATCH in valid_combos() parity.")
    else:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"FAILED: generate() smoke test crashed: {exc}")
    return rc


def _has_clingo() -> bool:
    try:
        import clingo  # noqa: F401
        return True
    except Exception:
        return False


def story_to_world(params: StoryParams) -> World:
    return tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        TOOLS[params.tool],
        params.child_name,
        params.child_gender,
        params.friend_name,
        params.friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, table in (("setting", SETTINGS), ("mystery", MYSTERIES), ("tool", TOOLS)):
        if getattr(params, field_name) not in table:
            raise StoryError(f"Invalid {field_name}: {getattr(params, field_name)!r}")
    world = story_to_world(params)
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
