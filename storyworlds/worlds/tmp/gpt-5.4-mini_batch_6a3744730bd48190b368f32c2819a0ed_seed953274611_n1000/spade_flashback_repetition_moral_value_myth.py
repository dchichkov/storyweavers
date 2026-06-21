#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spade_flashback_repetition_moral_value_myth.py
===============================================================================

A small mythic storyworld about a child, a spade, an old memory, and a moral
choice.  The domain is intentionally narrow: a spade is found in a garden or
courtyard, an old flashback reveals why it matters, repetition gives the tale a
myth-like rhythm, and the ending proves a moral value by showing what changed.

The engine is state-driven: characters, tools, places, and a remembered omen all
carry physical meters and emotional memes.  The story turns when the child
chooses whether to use the spade wisely, share it, or misuse it, and the ending
follows from those simulated state changes.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "goddess"}
        male = {"boy", "father", "man", "king", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    mood: str
    open_to_sky: bool = False
    sacred: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str
    sacred: bool = False
    sharp: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Omen:
    id: str
    sign: str
    lesson: str
    appears_in: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_used = False

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
        c.flashback_used = self.flashback_used
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child or child.memes["resolve"] < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["resolve"] += 1
    out.append("__repeat__")
    return out


def _r_moral_value(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    elder = world.entities.get("elder")
    if not child or not elder:
        return out
    if child.memes["share"] >= THRESHOLD and child.memes["respect"] >= THRESHOLD:
        sig = ("moral",)
        if sig not in world.fired:
            world.fired.add(sig)
            elder.memes["pride"] += 1
            child.memes["peace"] += 1
            out.append("__moral__")
    return out


CAUSAL_RULES = [Rule("repetition", _r_repetition), Rule("moral_value", _r_moral_value)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                lines.extend([s for s in out if not s.startswith("__")])
    if narrate:
        for line in lines:
            world.say(line)
    return lines


@dataclass
class StoryParams:
    place: str
    mood: str
    tool: str
    omen: str
    action: str
    lesson_path: str
    name: str
    elder_name: str
    name_gender: str
    elder_gender: str
    seed: Optional[int] = None


PLACES = {
    "garden": Place(id="garden", label="the garden", mood="green", open_to_sky=True, tags={"outdoor"}),
    "courtyard": Place(id="courtyard", label="the courtyard", mood="quiet", open_to_sky=True, sacred=True, tags={"stone"}),
    "well": Place(id="well", label="the old well", mood="still", open_to_sky=True, sacred=True, tags={"water"}),
}

TOOLS = {
    "spade": Tool(id="spade", label="spade", phrase="a little spade", purpose="dig", sharp=False, tags={"spade"}),
    "iron_spade": Tool(id="iron_spade", label="iron spade", phrase="an iron spade", purpose="dig deeper", sharp=True, tags={"spade"}),
}

OMENS = {
    "seedstone": Omen(id="seedstone", sign="a seed-stone", lesson="even a small tool can change a life", appears_in="the earth", tags={"memory"}),
    "moon_shard": Omen(id="moon_shard", sign="a moon shard", lesson="patient hands make better treasure", appears_in="the water", tags={"memory"}),
}

GIRL_NAMES = ["Mira", "Lena", "Sera", "Iris", "Nia", "Tala"]
BOY_NAMES = ["Aran", "Kian", "Noel", "Oren", "Bram", "Timo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES.values():
        for tool in TOOLS.values():
            for omen in OMENS.values():
                if place.sacred and tool.sharp:
                    continue
                combos.append((place.id, tool.id, omen.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld about a spade, a flashback, repetition, and moral value.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--omen", choices=sorted(OMENS))
    ap.add_argument("--action", choices=["dig", "share", "bury"])
    ap.add_argument("--lesson-path", choices=["wisdom", "kindness"])
    ap.add_argument("--name")
    ap.add_argument("--elder-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
              if (args.place is None or c[0] == args.place)
              and (args.tool is None or c[1] == args.tool)
              and (args.omen is None or c[2] == args.omen)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, omen = rng.choice(sorted(combos))
    action = args.action or rng.choice(["dig", "share", "bury"])
    lesson_path = args.lesson_path or rng.choice(["wisdom", "kindness"])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder_name = args.elder_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(place=place, mood=PLACES[place].mood, tool=tool, omen=omen, action=action,
                       lesson_path=lesson_path, name=name, elder_name=elder_name,
                       name_gender=gender, elder_gender=elder_gender)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.name_gender, role="child", label=params.name))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_gender, role="elder", label=params.elder_name))
    place = world.add(Entity(id=params.place, type="place", label=PLACES[params.place].label, tags=set(PLACES[params.place].tags)))
    tool = world.add(Entity(id=params.tool, type="tool", label=TOOLS[params.tool].label, tags=set(TOOLS[params.tool].tags)))
    omen = world.add(Entity(id=params.omen, type="omen", label=OMENS[params.omen].sign, attrs={"lesson": OMENS[params.omen].lesson}))

    child.memes["curiosity"] = 1
    elder.memes["care"] = 1

    world.say(f"Once, in {place.label}, {child.label} found {tool.phrase}.")
    world.say(f"The place was {params.mood}, and the little spade felt like a gift from the old stories.")
    world.say(f"{child.label} held it up and asked whether the earth would open its heart.")

    world.para()
    world.say(f"Long before that day, {elder.label} had told a tale: {omen.sign} had once lain in the earth.")
    world.say(f"In that old tale, the first lesson was always the same: {OMENS[params.omen].lesson}.")
    world.flashback_used = True

    world.para()
    if params.action == "dig":
        child.memes["resolve"] += 1
        world.say(f"So {child.label} began to dig, and dig, and dig, careful not to waste a single handful of soil.")
        if params.place == "well":
            child.meters["risk"] += 1
            world.say("But the well was sacred, and the ground felt wrong beneath the spade.")
            world.say(f"{elder.label} lifted a hand and said the old warning again: respect what keeps the village safe.")
        else:
            world.say(f"The earth loosened, and a small root curled up like a brown snake of luck.")
    elif params.action == "share":
        child.memes["share"] += 1
        child.memes["respect"] += 1
        world.say(f"So {child.label} carried the spade to {elder.label} and shared the work.")
        world.say("Together they turned the soil gently, and the garden seemed to listen.")
    else:
        child.memes["respect"] += 1
        world.say(f"So {child.label} buried the omen-stone again and left the roots undisturbed.")
        world.say("The ground closed softly, like a secret being kept with care.")

    if params.action == "dig":
        child.memes["resolve"] += 1
    if params.action == "share":
        child.memes["share"] += 1
        child.memes["respect"] += 1

    propagate(world, narrate=False)

    world.para()
    if child.memes["peace"] >= THRESHOLD or params.action == "share":
        world.say(f"Then the child learned, as the elders always said, that strength without kindness is only noise.")
        world.say(f"So {child.label} and {elder.label} repeated the promise: use the spade, but use it well; use the spade, but use it well.")
        world.say(f"At sunset the spade leaned beside the wall, clean in the gold light, and the child felt wiser than before.")
    else:
        world.say(f"Then the child learned that some doors should not be forced open.")
        world.say(f"The elder repeated the old truth: use the spade, but use it well; use the spade, but use it well.")
        world.say(f"At sunset the spade rested by the door, and the child bowed to the lesson, quiet and changed.")

    world.facts.update(params=params, child=child, elder=elder, place=place, tool=tool, omen=omen,
                       outcome="moral", flashback=world.flashback_used)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f"Write a mythic children's story that includes the word 'spade' and ends with a clear moral lesson.",
        f"Tell a story about {p.name} and an elder in {PLACES[p.place].label} where an old memory changes how the spade is used.",
        f"Write a repetitive, flashback-filled myth for a young child showing why {p.name} should use the spade wisely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    p: StoryParams = f["params"]
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    qa = [
        ("Who is the story about?", f"It is about {child.label} and {elder.label}, and the little spade that changed their day."),
        ("What old memory appears in the story?", f"There is a flashback to an earlier tale about {f['omen'].label}, and it reminds the child that {f['omen'].attrs['lesson']}."),
        ("What repeated line matters most?", "The tale repeats the warning to use the spade wisely. The repetition turns the warning into a chant the child can remember."),
    ]
    if child.memes["peace"] >= THRESHOLD or p.action == "share":
        qa.append(("What moral does the story teach?", "It teaches that strength should be guided by kindness and respect. The child proves that wisdom matters more than taking things by force."))
    else:
        qa.append(("What moral does the story teach?", "It teaches that some actions should stop when they would harm what is sacred. The child learns to respect the old place instead of forcing the earth open."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a spade?", "A spade is a tool with a flat blade for digging in earth. People use it to move soil carefully."),
        ("What is a flashback?", "A flashback is a story moment that shows something from earlier. It helps explain why a character acts a certain way now."),
        ("Why do stories repeat lines?", "Repetition makes a message easy to remember. In old myth-like stories, repeated lines can feel solemn and important."),
        ("What is a moral value?", "A moral value is a lesson about how to live well, like kindness, respect, or honesty. Stories often end by showing that value in action."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", mood=PLACES["garden"].mood, tool="spade", omen="seedstone", action="share",
                lesson_path="kindness", name="Mira", elder_name="Tala", name_gender="girl", elder_gender="woman"),
    StoryParams(place="courtyard", mood=PLACES["courtyard"].mood, tool="spade", omen="moon_shard", action="dig",
                lesson_path="wisdom", name="Aran", elder_name="Bram", name_gender="boy", elder_gender="man"),
    StoryParams(place="well", mood=PLACES["well"].mood, tool="spade", omen="seedstone", action="bury",
                lesson_path="wisdom", name="Nia", elder_name="Iris", name_gender="girl", elder_gender="woman"),
]


def explain_rejection(place: Place, tool: Tool) -> str:
    if place.sacred and tool.sharp:
        return f"(No story: {tool.label} is too sharp for {place.label}. A sacred place needs a gentler choice.)"
    return "(No story: this combination does not fit the mythic story rules.)"


def valid_story_params(p: StoryParams) -> bool:
    if p.place not in PLACES or p.tool not in TOOLS or p.omen not in OMENS:
        return False
    place, tool = PLACES[p.place], TOOLS[p.tool]
    if place.sacred and tool.sharp:
        return False
    return True


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.sacred:
            lines.append(asp.fact("sacred", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.sharp:
            lines.append(asp.fact("sharp", tid))
    for oid in OMENS:
        lines.append(asp.fact("omen", oid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,O) :- place(P), tool(T), omen(O), not bad(P,T).
bad(P,T) :- sacred(P), sharp(T).
"""


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if not valid_story_params(params):
        raise StoryError("Invalid parameters for this mythic world.")
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combinations:")
        for combo in asp_valid_combos():
            print("  ", combo)
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
        header = "### curated myth" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else "")
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
