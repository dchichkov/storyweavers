#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/battery_sharing_reconciliation_rhyming_story.py
===============================================================================

A small storyworld about a battery-powered toy, a sharing quarrel, and a warm
reconciliation. The stories are child-facing, concrete, and lightly rhyming.

The premise is simple:
- one child has a battery-powered toy,
- another child wants a turn,
- feelings rise when the toy is held too tightly,
- a grown-up or a wise child helps them share,
- the children make up and play together.

The narration aims for a gentle rhyming-story feel without forcing every line
to rhyme. The simulation drives the prose: who is holding the toy, whose turn it
is, how upset each child feels, and whether they reconcile before the ending.

This file is standalone and uses only the Python standard library plus the shared
result containers and optional ASP helper from the Storyweavers repo.
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
START_CHEER = 5.0
START_WAIT = 0.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    battery: bool = False
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    rhyme_hint: str
    mood: str
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


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    sound: str
    battery: bool = True
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
class ShareResponse:
    id: str
    text: str
    resolve_text: str
    power: int
    sense: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_escalate(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("toy")
    holder = world.get("holder")
    waiter = world.get("waiter")
    if toy.meters["held"] >= THRESHOLD and waiter.memes["sad"] >= THRESHOLD:
        sig = ("escalate", toy.id, holder.id, waiter.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        holder.memes["stubborn"] += 1
        waiter.memes["hurt"] += 1
        out.append("__tension__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("toy")
    holder = world.get("holder")
    waiter = world.get("waiter")
    if toy.meters["shared"] >= THRESHOLD and holder.memes["kind"] >= THRESHOLD and waiter.memes["kind"] >= THRESHOLD:
        sig = ("reconcile", toy.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        holder.memes["joy"] += 1
        waiter.memes["joy"] += 1
        holder.memes["hurt"] = 0.0
        waiter.memes["hurt"] = 0.0
        out.append("__peace__")
    return out


CAUSAL_RULES = [Rule("escalate", _r_escalate), Rule("reconcile", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def predict_scene(world: World) -> dict:
    sim = world.copy()
    toy = sim.get("toy")
    holder = sim.get("holder")
    waiter = sim.get("waiter")
    toy.meters["held"] = 1.0
    waiter.memes["sad"] += 1
    propagate(sim, narrate=False)
    return {
        "tension": holder.memes["stubborn"] + waiter.memes["hurt"],
        "shared": toy.meters["shared"] >= THRESHOLD,
    }


def _hold_tight(world: World, holder: Entity, toy: Entity) -> None:
    toy.meters["held"] += 1
    holder.memes["joy"] += 1
    world.say(
        f"{holder.id} found a bright little toy, a battery-powered delight. "
        f"{toy.label_word.capitalize()} blinked and beeped in the soft afternoon light."
    )


def _ask_share(world: World, waiter: Entity, holder: Entity, toy: Entity) -> None:
    waiter.memes["sad"] += 1
    pred = predict_scene(world)
    world.facts["predicted_tension"] = pred["tension"]
    world.say(
        f'"May I have a turn?" asked {waiter.id} with a hopeful grin. '
        f'"I want to hear the beep-beep song and join the fun within."'
    )
    world.say(
        f"{holder.id} hugged {toy.label_word} close and frowned a tiny frown; "
        f"the room grew tight and quiet, like clouds that tugged night down."
    )


def _refuse(world: World, holder: Entity, waiter: Entity, toy: Entity) -> None:
    holder.memes["stubborn"] += 1
    world.say(
        f'"No, it is mine," said {holder.id}, holding on with all {holder.pronoun("possessive")} might. '
        f"But the toy still sparkled warmly, and that did not make things right."
    )


def _wise_step(world: World, helper: Entity, holder: Entity, waiter: Entity, toy: Entity) -> None:
    helper.memes["kind"] += 1
    world.say(
        f"{helper.id} came with a gentle smile and a voice both soft and clear: "
        f'"Sharing makes the game shine brighter, and everyone gets cheer."'
    )


def _share_turns(world: World, holder: Entity, waiter: Entity, toy: Entity) -> None:
    toy.meters["shared"] += 1
    holder.memes["kind"] += 1
    waiter.memes["kind"] += 1
    world.say(
        f"{holder.id} gave {waiter.id} a turn at last, and the toy beeped out its tune. "
        f"They passed it back and forth like a song beneath the moon."
    )
    propagate(world, narrate=False)


def _reconcile(world: World, helper: Entity, holder: Entity, waiter: Entity, toy: Entity) -> None:
    world.say(
        f"{helper.id} smiled and nodded once; the hard part drifted away. "
        f"{holder.id} and {waiter.id} looked at each other, then began to say:"
    )
    world.say(
        f'"Sorry," whispered {holder.id}. "I was grumpy and unfair." '
        f'"Sorry too," said {waiter.id}, "for making such a sad little air."'
    )
    world.say(
        f"They bumped hands, then laughed a bit, and the toy flashed on and on. "
        f"The squabble was now over, and the sharp hurt feeling gone."
    )


def tell(setting: Setting, toy: Toy, holder_name: str = "Milo", holder_gender: str = "boy",
         waiter_name: str = "Nia", waiter_gender: str = "girl",
         helper_name: str = "Mom", helper_gender: str = "mother") -> World:
    world = World()
    holder = world.add(Entity(id=holder_name, kind="character", type=holder_gender, role="holder"))
    waiter = world.add(Entity(id=waiter_name, kind="character", type=waiter_gender, role="waiter"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    t = world.add(Entity(id="toy", type="toy", label=toy.label, battery=toy.battery))
    holder.memes["joy"] = START_CHEER
    waiter.memes["joy"] = START_WAIT
    helper.memes["kind"] = 1.0
    world.facts["setting"] = setting
    world.facts["toy_cfg"] = toy

    world.say(
        f"In {setting.place}, the day was fair, with a warm and breezy tune. "
        f"{holder.id} had {toy.phrase}, a battery toy that sang a merry croon."
    )
    world.say(
        f"{waiter.id} watched the blinking lights and wanted in the play, "
        f"for sharing a good bright toy can make the longest day."
    )

    world.para()
    _hold_tight(world, holder, t)
    _ask_share(world, waiter, holder, t)
    _refuse(world, holder, waiter, t)

    world.para()
    _wise_step(world, helper, holder, waiter, t)
    _share_turns(world, holder, waiter, t)
    _reconcile(world, helper, holder, waiter, t)

    world.facts.update(
        holder=holder,
        waiter=waiter,
        helper=helper,
        toy=t,
        shared=t.meters["shared"] >= THRESHOLD,
        reconciled=True,
    )
    return world


SETTINGS = {
    "bedroom": Setting(id="bedroom", place="the bedroom", rhyme_hint="light", mood="bright"),
    "playroom": Setting(id="playroom", place="the playroom", rhyme_hint="play", mood="gay"),
    "backyard": Setting(id="backyard", place="the backyard", rhyme_hint="day", mood="warm"),
}

TOYS = {
    "robot": Toy(id="robot", label="robot", phrase="a little robot", sound="beep-beep", tags={"toy", "share"}),
    "car": Toy(id="car", label="toy car", phrase="a battery toy car", sound="vroom-buzz", tags={"toy", "share"}),
    "drum": Toy(id="drum", label="drum", phrase="a batter-powered drum", sound="boom-buzz", tags={"toy", "share"}),
}

RESPONSES = {
    "gentle": ShareResponse(
        id="gentle",
        text="smiled, set the toy down, and asked the children to take turns",
        resolve_text="helped them share and make up",
        power=2,
        sense=3,
    ),
    "coach": ShareResponse(
        id="coach",
        text="showed them a turn-taking trick: one count of five, then switch",
        resolve_text="helped them take turns and feel better",
        power=3,
        sense=3,
    ),
}


@dataclass
class StoryParams:
    setting: str
    toy: str
    holder_name: str
    holder_gender: str
    waiter_name: str
    waiter_gender: str
    helper_name: str
    helper_gender: str
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
    StoryParams(
        setting="playroom",
        toy="robot",
        holder_name="Milo",
        holder_gender="boy",
        waiter_name="Nia",
        waiter_gender="girl",
        helper_name="Mom",
        helper_gender="mother",
    ),
    StoryParams(
        setting="backyard",
        toy="car",
        holder_name="Ava",
        holder_gender="girl",
        waiter_name="Ben",
        waiter_gender="boy",
        helper_name="Dad",
        helper_gender="father",
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in TOYS if TOYS[t].battery]


def explain_rejection(setting_id: str, toy_id: str) -> str:
    if setting_id not in SETTINGS or toy_id not in TOYS:
        return "(No story: unknown setting or toy.)"
    return "(No story: this world needs a battery-powered toy so sharing can be shown clearly.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Battery-sharing reconciliation rhyming storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--holder-name")
    ap.add_argument("--waiter-name")
    ap.add_argument("--helper-name")
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
    if args.setting and args.toy:
        if not TOYS[args.toy].battery:
            raise StoryError(explain_rejection(args.setting, args.toy))
    combos = [c for c in valid_combos()
              if args.setting is None or c[0] == args.setting
              if args.toy is None or c[1] == args.toy]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, toy = rng.choice(sorted(combos))
    names_b = ["Milo", "Noah", "Theo", "Ben", "Leo"]
    names_g = ["Nia", "Ava", "Mia", "Zoe", "Luna"]
    return StoryParams(
        setting=setting,
        toy=toy,
        holder_name=args.holder_name or rng.choice(names_b + names_g),
        holder_gender="boy" if (args.holder_name or "").startswith(("M", "N", "T", "B", "L")) else "girl",
        waiter_name=args.waiter_name or rng.choice(names_b + names_g),
        waiter_gender="girl" if (args.waiter_name or "").startswith(("N", "A", "M", "Z", "L")) else "boy",
        helper_name=args.helper_name or rng.choice(["Mom", "Dad", "Auntie"]),
        helper_gender="mother",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle rhyming story for a 3-to-5-year-old that includes the word "{f["toy"].label}".',
        "Tell a story about sharing a battery-powered toy, a small quarrel, and then making up.",
        "Write a rhyming story where two children learn to take turns and reconcile after a disagreement.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    holder = f["holder"]
    waiter = f["waiter"]
    toy = f["toy"]
    helper = f["helper"]
    return [
        ("Who had the battery-powered toy at the start?",
         f"{holder.id} had the {toy.label} at the start, and the toy blinked and beeped in the room."),
        (f"Why did {waiter.id} feel upset?",
         f"{waiter.id} felt upset because {waiter.id} wanted a turn and was waiting while {holder.id} held on tight. That made the room feel tense until a grown-up helped them share."),
        ("How did they fix the problem?",
         f"{helper.id} helped them take turns with the toy, and then they said sorry and played together again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a battery?",
         "A battery gives power to toys and other small things so they can blink, beep, or move."),
        ("What does sharing mean?",
         "Sharing means letting someone else use something too. It helps people play together."),
        ("What does reconciliation mean?",
         "Reconciliation means making up after a disagreement so people can be kind again."),
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
        if e.battery:
            bits.append("battery=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
battery_toy(T) :- toy(T), battery(T).
shared(T) :- toy(T), shared_turn(T).
reconciled(T) :- shared(T), kind(holder), kind(waiter).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, toy in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if toy.battery:
            lines.append(asp.fact("battery", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show battery_toy/1."))
    return sorted(set(asp.atoms(model, "battery_toy")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((tid,) for tid in TOYS):
        rc = 1
        print("MISMATCH: ASP and Python valid combos differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.toy not in TOYS:
        raise StoryError("Unknown toy.")
    world = tell(
        SETTINGS[params.setting],
        TOYS[params.toy],
        holder_name=params.holder_name,
        holder_gender=params.holder_gender,
        waiter_name=params.waiter_name,
        waiter_gender=params.waiter_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
    )
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
        print(asp_program("", "#show battery_toy/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(t[0] for t in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
