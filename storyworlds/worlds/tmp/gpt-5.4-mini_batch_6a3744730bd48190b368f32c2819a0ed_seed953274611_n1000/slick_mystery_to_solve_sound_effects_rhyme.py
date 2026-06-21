#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slick_mystery_to_solve_sound_effects_rhyme.py
===============================================================================

A tiny comedy mystery storyworld: a child detective solves a silly "slick" clue,
with sound effects and playful rhyme. The world is state-driven: clues, suspects,
noisy mishaps, and a final reveal change the physical and emotional meters.

The domain is intentionally small and child-facing:
- a snack, a spilled slick trail, and a missing treat,
- one or two helpers,
- a comic culprit or a mistaken misunderstanding,
- a cozy ending image that proves the mystery was solved.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/slick_mystery_to_solve_sound_effects_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/slick_mystery_to_solve_sound_effects_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/slick_mystery_to_solve_sound_effects_rhyme.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
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


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    clue_zone: str


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    type: str
    risky: bool = False
    slick: bool = False
    noisy: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    alibi: str
    sound: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_slick(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["slippery"] < THRESHOLD:
            continue
        sig = ("slick", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.characters():
            c.memes["alert"] += 1
        out.append("Slick! The detective knew this clue was important.")
    return out


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["noisy"] < THRESHOLD:
            continue
        sig = ("noise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.characters():
            c.memes["curiosity"] += 1
        out.append("Bop-bop-bop! Another clue popped up.")
    return out


CAUSAL_RULES = [Rule("slick", _r_slick), Rule("noise", _r_noise)]


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


def predict(world: World, clue_id: str) -> dict:
    sim = world.copy()
    sim.get(clue_id).meters["slippery"] += 1
    propagate(sim, narrate=False)
    return {
        "alert": sim.get("detective").memes["alert"],
        "curiosity": sim.get("detective").memes["curiosity"],
    }


def intro(world: World, detective: Entity, sidekick: Entity, setting: Setting) -> None:
    detective.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {detective.id} and {sidekick.id} turned {setting.place} "
        f"into a tiny mystery town. {setting.scene}"
    )
    world.say(
        f'"We need to solve the mystery!" {detective.id} said. '
        f'"Then maybe we will find something slick."'
    )


def clue(world: World, setting: Setting, track: Thing) -> None:
    world.say(
        f"Near the {setting.clue_zone}, they found a {track.label} trail. "
        f"It was so {track.label} that even the floor seemed to wink."
    )


def suspecting(world: World, detective: Entity, suspect: Suspect) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f'"Could it be {suspect.label}?" {detective.id} asked. '
        f'"{suspect.sound}! {suspect.rhyme}!"'
    )


def suspect_response(world: World, sidekick: Entity, suspect: Suspect) -> None:
    world.say(
        f'{sidekick.id} pointed and giggled. "{suspect.alibi}" '
        f"{suspect.sound} went the {suspect.label}."
    )


def reveal(world: World, detective: Entity, culprit: Entity, prize: Thing) -> None:
    culprit.memes["relief"] += 1
    detective.memes["pride"] += 1
    prize.meters["found"] += 1
    world.say(
        f'Then the truth rolled out: {culprit.id} had tucked the {prize.label} '
        f"behind the snack box. It had made the floor slick, and the whole mystery "
        f"had been a crumbly comedy."
    )
    world.say(
        f'"Aha!" said {detective.id}. "No monster, no trick -- just a snack attack!"'
    )


def ending(world: World, detective: Entity, sidekick: Entity, prize: Thing, setting: Setting) -> None:
    detective.memes["satisfaction"] += 1
    sidekick.memes["satisfaction"] += 1
    world.say(
        f"They wiped the slick spot clean, shared the {prize.label}, and laughed "
        f"until the whole {setting.place} felt like a joke with a happy ending."
    )
    world.say(
        f"At last, {detective.id} wore a grin as shiny as the floor had been slick."
    )


def tell(setting: Setting, track: Thing, suspect: Suspect, prankster_name: str,
         owner_name: str, sidekick_name: str) -> World:
    world = World()
    detective = world.add(Entity(id=owner_name, kind="character", type="boy", role="detective"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="girl", role="sidekick"))
    prankster = world.add(Entity(id=prankster_name, kind="character", type="boy", role="prankster"))
    snack = world.add(Entity(id="snack", type="thing", label=track.label))
    world.facts["setting"] = setting
    world.facts["track"] = track
    world.facts["suspect"] = suspect
    world.facts["prankster"] = prankster
    world.facts["detective"] = detective
    world.facts["sidekick"] = sidekick
    world.facts["snack"] = snack

    intro(world, detective, sidekick, setting)
    world.para()
    clue(world, setting, track)
    pred = predict(world, "snack")
    world.facts["pred"] = pred
    suspecting(world, detective, suspect)
    suspect_response(world, sidekick, suspect)
    world.para()
    snack.meters["slippery"] += 1
    track.meters["slippery"] += 1
    track.meters["noisy"] += 1
    propagate(world, narrate=True)
    reveal(world, detective, prankster, track)
    ending(world, detective, sidekick, track, setting)
    world.facts["outcome"] = "solved"
    return world


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        scene="The spoon rack looked like a row of tiny microphones, and the tiles were bright as gumdrops.",
        clue_zone="cookie jar",
    ),
    "bakery": Setting(
        id="bakery",
        place="the bakery",
        scene="The oven chimed, the pastry case sparkled, and flour floated around like sleepy snow.",
        clue_zone="counter",
    ),
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        scene="The chalkboard waited like a stage, and the reading rug was a square of quiet courage.",
        clue_zone="supply shelf",
    ),
}

TRACKS = {
    "jam": Thing(
        id="jam",
        label="jam",
        phrase="a jam jar",
        type="thing",
        risky=True,
        slick=True,
        noisy=False,
        tags={"slick", "food"},
    ),
    "soap": Thing(
        id="soap",
        label="soap",
        phrase="a soap bar",
        type="thing",
        risky=True,
        slick=True,
        noisy=False,
        tags={"slick", "bath"},
    ),
    "soda": Thing(
        id="soda",
        label="soda",
        phrase="a soda can",
        type="thing",
        risky=True,
        slick=True,
        noisy=True,
        tags={"slick", "pop"},
    ),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the cat",
        phrase="a cat",
        alibi="I was napping in a basket.",
        sound="Purr",
        rhyme="curl and whirl",
        tags={"cat", "comedy"},
    ),
    "robot": Suspect(
        id="robot",
        label="the robot",
        phrase="a robot",
        alibi="I was charging quietly by the wall.",
        sound="Beep",
        rhyme="sleep and sweep",
        tags={"robot", "comedy"},
    ),
    "duck": Suspect(
        id="duck",
        label="the duck",
        phrase="a duck",
        alibi="I was only quacking for crackers.",
        sound="Quack",
        rhyme="snack and track",
        tags={"duck", "comedy"},
    ),
}

CURATED = [
    StoryParams(
        setting="kitchen",
        track="jam",
        suspect="cat",
        prankster="Milo",
        owner="Ned",
        sidekick="Pia",
        seed=1,
    ),
    StoryParams(
        setting="bakery",
        track="soap",
        suspect="duck",
        prankster="Bram",
        owner="Jun",
        sidekick="Lena",
        seed=2,
    ),
    StoryParams(
        setting="classroom",
        track="soda",
        suspect="robot",
        prankster="Otis",
        owner="Cal",
        sidekick="Tia",
        seed=3,
    ),
]


@dataclass
class StoryParams:
    setting: str
    track: str
    suspect: str
    prankster: str
    owner: str
    sidekick: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TRACKS:
            for u in SUSPECTS:
                combos.append((s, t, u))
    return combos


KNOWLEDGE = {
    "slick": [("What does slick mean?",
               "Slick means smooth and slippery. A slick floor can make feet slide around.")],
    "jam": [("What is jam?",
             "Jam is a sweet fruit spread. It can make a surface sticky and messy if it spills.")],
    "soap": [("What is soap for?",
              "Soap helps clean hands and wash away dirt. It can also make things slippery when wet.")],
    "soda": [("Why can soda be messy?",
              "Soda bubbles and spills easily, so it can make a sticky wet puddle.")],
    "cat": [("What does a cat say?",
             "A cat says meow or purr. Cats are often quiet and silly in stories.")],
    "robot": [("What is a robot?",
                "A robot is a machine that can move or make noises. Stories often give robots funny voices.")],
    "duck": [("What does a duck say?",
              "A duck says quack. Ducks are often used in funny stories because they sound so cheerful.")],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy mystery storyworld with slick clues, sound effects, and rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--track", choices=TRACKS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--prankster")
    ap.add_argument("--owner")
    ap.add_argument("--sidekick")
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
              and (args.track is None or c[1] == args.track)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, track, suspect = rng.choice(combos)
    return StoryParams(
        setting=setting,
        track=track,
        suspect=suspect,
        prankster=args.prankster or rng.choice(["Milo", "Bram", "Otis", "Nia"]),
        owner=args.owner or rng.choice(["Ned", "Jun", "Cal", "Ada"]),
        sidekick=args.sidekick or rng.choice(["Pia", "Lena", "Tia", "Zoe"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny mystery story for a 3-to-5-year-old that includes the word "{f["track"].label}" and the word "slick".',
        f"Tell a comedy detective story where {f['detective'].id} and {f['sidekick'].id} solve a mystery with sound effects and a rhyme.",
        f"Write a playful story in which a silly clue turns out to be {f['track'].label}, and the ending explains the prank in a gentle way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    sidekick = f["sidekick"]
    track = f["track"]
    prankster = f["prankster"]
    setting = f["setting"]
    suspect = f["suspect"]
    return [
        QAItem(
            question="What mystery did they solve?",
            answer=f"They solved the mystery of the slick clue. It turned out the shiny mess came from {track.label}, not from a scary monster.",
        ),
        QAItem(
            question="Who made the mess?",
            answer=f"{prankster.id} made the mess by hiding the {track.label} behind the snack box. It was a silly prank, so the story stays funny instead of scary.",
        ),
        QAItem(
            question=f"What did {detective.id} and {sidekick.id} do at the end?",
            answer=f"They cleaned the slick spot, found the {track.label}, and laughed together in {setting.place}. That ending proves the mystery was solved and everyone was fine.",
        ),
        QAItem(
            question=f"What sound did {suspect.label} make?",
            answer=f"{suspect.sound}! {suspect.alibi}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["track"].tags)
    tags |= set(world.facts["suspect"].tags)
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            for q, a in items:
                out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def tell_story(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    track = TRACKS[params.track]
    suspect = SUSPECTS[params.suspect]
    world = World()
    detective = world.add(Entity(id=params.owner, kind="character", type="boy", role="detective"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="girl", role="sidekick"))
    prankster = world.add(Entity(id=params.prankster, kind="character", type="boy", role="prankster"))
    clue = world.add(Entity(id="clue", type="thing", label=track.label, tags=set(track.tags)))
    world.facts.update(setting=setting, track=track, suspect=suspect, prankster=prankster, detective=detective, sidekick=sidekick, clue=clue)

    intro(world, detective, sidekick, setting)
    world.para()
    clue.meters["slippery"] += 1
    clue.meters["noisy"] += 1 if track.noisy else 0
    clue(world, setting, track)
    suspecting(world, detective, suspect)
    suspect_response(world, sidekick, suspect)
    propagate(world, narrate=True)
    world.para()
    reveal(world, detective, prankster, track)
    ending(world, detective, sidekick, track, setting)
    world.facts["outcome"] = "solved"
    return world


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.track not in TRACKS or params.suspect not in SUSPECTS:
        raise StoryError("Invalid parameters.")
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
slick(X) :- slippery(X).
noisy(X) :- noisy_fact(X).
solve :- slick(clue), noisy(clue).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TRACKS.items():
        lines.append(asp.fact("track", tid))
        if t.slick:
            lines.append(asp.fact("slippery", tid))
        if t.noisy:
            lines.append(asp.fact("noisy_fact", tid))
    for uid in SUSPECTS:
        lines.append(asp.fact("suspect", uid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show track/1.\n#show suspect/1.\n"))
    # this world is fully permissive; combinations are the cartesian product
    return sorted(set((s[0], t[0], u[0]) for s in asp.atoms(model, "setting") for t in asp.atoms(model, "track") for u in asp.atoms(model, "suspect")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH: ASP and Python combo sets differ.")
        rc = 1
    else:
        print(f"OK: combo parity with ASP ({len(py)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: default generate smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate smoke test crashed: {exc}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show setting/1.\n#show track/1.\n#show suspect/1."))
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
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
