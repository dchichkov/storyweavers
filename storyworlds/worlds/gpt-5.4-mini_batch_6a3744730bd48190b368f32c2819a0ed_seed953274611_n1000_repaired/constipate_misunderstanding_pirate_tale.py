#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/constipate_misunderstanding_pirate_tale.py
===========================================================================

A tiny standalone storyworld about a pirate crew, a confusing word, and a
friendly correction. The seed word "constipate" is treated as a silly
misunderstood word in a pirate setting: one child thinks it is a ship action,
another realizes it means a belly problem, and a grown-up clears up the mix-up.

The world is small on purpose:
- typed entities with physical meters and emotional memes
- a short causal simulation that changes the story state
- grounded Q&A from the simulated world
- a Python reasonableness gate and an inline ASP twin
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    dark_spot: str
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
class Misunderstanding:
    id: str
    word: str
    wrong_guess: str
    clue_line: str
    reveal_line: str
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
class Response:
    id: str
    sense: int
    text: str
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
class StoryParams:
    setting: str
    misunderstanding: str
    response: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    adult: str
    adult_type: str
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
        clone.facts = dict(self.facts)
        return clone


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


def _r_belly(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["hunger"] >= THRESHOLD and ("misread_word" in ent.tags):
            sig = ("belly", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["worry"] += 1
            out.append("__belly__")
    return out


CAUSAL_RULES = [Rule("belly", _r_belly)]


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


def resolve_misunderstanding(world: World, child: Entity, helper: Entity, adult: Entity,
                             ms: Misunderstanding, response: Response) -> None:
    child.memes["confusion"] += 1
    helper.memes["alarm"] += 1
    world.say(
        f"On a windy afternoon aboard {world.get('ship').label}, {child.id} found a funny word in a note: "
        f"“{ms.word}.”"
    )
    world.say(
        f'{child.id} frowned. "{ms.word}?" {child.pronoun()} said. '
        f'"That sounds like it should {ms.wrong_guess}!"'
    )
    world.say(
        f"{helper.id} blinked hard, then pointed at the clue: {ms.clue_line}"
    )


def confuse(world: World, child: Entity, helper: Entity, ms: Misunderstanding) -> None:
    child.tags.add("misread_word")
    child.meters["hunger"] += 1
    child.memes["silliness"] += 1
    world.say(
        f"{child.id} laughed and tried to use the word in a pirate way. "
        f'"Maybe it means to {ms.wrong_guess}," {child.id} said, “like when a ship gets stuck!”'
    )


def warn(world: World, helper: Entity, child: Entity, ms: Misunderstanding) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. '
        f'"I think {ms.word} means a belly problem, not a ship trick."'
    )
    world.say(
        f"{helper.id} sounded unsure at first, because big words can be tricky on a ship."
    )


def reveal(world: World, adult: Entity, child: Entity, helper: Entity,
           ms: Misunderstanding, response: Response) -> None:
    adult.memes["calm"] += 1
    body = response.text
    world.say(
        f"{adult.label_word.capitalize()} came over, smiled, and explained it plainly: {ms.reveal_line}"
    )
    world.say(
        f'In no time, {adult.id} {body}, and the mix-up stopped feeling scary.'
    )
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["confusion"] = 0.0


def ending(world: World, child: Entity, helper: Entity, adult: Entity, ms: Misunderstanding) -> None:
    world.say(
        f"After that, {child.id} and {helper.id} made a silly rule: if a word sounds odd, ask a grown-up before guessing."
    )
    world.say(
        f"They sailed on with cleaner heads, a warmer laugh, and the word “{ms.word}” tucked away as a new lesson."
    )


SETTINGS = {
    "deck": Setting(
        id="deck",
        place="the deck",
        scene="a pirate game with a map, a rope coil, and a cardboard telescope",
        dark_spot="the shadow by the cargo crate",
        tags={"pirate", "ship"},
    ),
    "cabin": Setting(
        id="cabin",
        place="the cabin",
        scene="a pretend ship room with a lantern, a blanket sail, and a toy chest",
        dark_spot="the corner under the bunk",
        tags={"pirate", "ship"},
    ),
}

MISUNDERSTANDINGS = {
    "constipate": Misunderstanding(
        id="constipate",
        word="constipate",
        wrong_guess="constipate the sails",
        clue_line="The note said, 'When your belly hurts, you might feel constipate.'",
        reveal_line="It means someone has a belly that feels blocked and uncomfortable, not a pirate command at all.",
        tags={"word", "body", "pirate"},
    ),
}

RESPONSES = {
    "laugh": Response(
        id="laugh",
        sense=3,
        text="laughed softly and handed over a cup of warm water",
        tags={"calm"},
    ),
    "explain": Response(
        id="explain",
        sense=4,
        text="explained the word without making it sound big and scary",
        tags={"calm"},
    ),
}

CHILDREN = [("Mina", "girl"), ("Jasper", "boy"), ("Luna", "girl"), ("Owen", "boy")]
HELPERS = [("Pip", "boy"), ("Nell", "girl"), ("Toby", "boy"), ("Rose", "girl")]
ADULTS = [("Captain Mara", "mother"), ("Captain Eli", "father")]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MISUNDERSTANDINGS:
            for rid, resp in RESPONSES.items():
                if resp.sense >= 2:
                    combos.append((sid, mid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate misunderstanding storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-type", choices=["mother", "father"])
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("That response is too silly to count as a calm explanation.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.misunderstanding is None or c[1] == args.misunderstanding)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, misunderstanding, response = rng.choice(sorted(combos))
    child, child_type = (args.child, args.child_type) if args.child and args.child_type else rng.choice(CHILDREN)
    helper, helper_type = (args.helper, args.helper_type) if args.helper and args.helper_type else rng.choice([h for h in HELPERS if h[1] != child_type])
    adult, adult_type = (args.adult, args.adult_type) if args.adult and args.adult_type else rng.choice(ADULTS)
    return StoryParams(
        setting=setting,
        misunderstanding=misunderstanding,
        response=response,
        child=child,
        child_type=child_type,
        helper=helper,
        helper_type=helper_type,
        adult=adult,
        adult_type=adult_type,
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    ms = MISUNDERSTANDINGS[params.misunderstanding]
    resp = RESPONSES[params.response]
    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult_type, role="adult", label=f"{params.adult}"))
    ship = world.add(Entity(id="ship", type="ship", label="the ship"))
    world.facts.update(setting=setting, ms=ms, resp=resp, child=child, helper=helper, adult=adult, ship=ship)
    world.say(
        f"{child.id} and {helper.id} were aboard {setting.place}, where the crew loved to play pretend under the salt wind."
    )
    world.say(
        f"They found a note with the word “{ms.word},” and {child.id} tried to guess it from the sound alone."
    )
    world.para()
    resolve_misunderstanding(world, child, helper, adult, ms, resp)
    confuse(world, child, helper, ms)
    warn(world, helper, child, ms)
    reveal(world, adult, child, helper, ms, resp)
    world.para()
    ending(world, child, helper, adult, ms)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    ms = world.facts["ms"]
    return [
        f'Write a pirate story for a 3-to-5-year-old that includes the word "{ms.word}" and begins with a misunderstanding.',
        f'Tell a gentle pirate tale where a child guesses what "{ms.word}" means, gets it wrong, and then learns the true meaning from a grown-up.',
        f'Write a small story with a misunderstanding on a ship and a calm correction that uses the word "{ms.word}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    ms = world.facts["ms"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    adult = world.facts["adult"]
    return [
        QAItem(
            question=f"What word confused {child.id}?",
            answer=f"The confusing word was “{ms.word}.” {child.id} only guessed from how it sounded, so the meaning got смеш? no. It turned into a pirate misunderstanding until {adult.id} explained it.",
        ),
        QAItem(
            question=f"What did {child.id} think {ms.word} meant?",
            answer=f"{child.id} thought it meant to {ms.wrong_guess}. That guess fit a pirate game in {world.facts['setting'].place}, but it was not the real meaning.",
        ),
        QAItem(
            question="How was the misunderstanding fixed?",
            answer=f"{adult.id} explained the word plainly, and {helper.id} helped by pointing to the clue. After that, everyone felt relieved and the story turned calm again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does constipate mean?",
            answer="It means a belly feels blocked and uncomfortable, so a person may have trouble going to the bathroom. It is not a pirate command or a ship action.",
        ),
        QAItem(
            question="What should you do when you hear a word you do not know?",
            answer="You should ask a grown-up or check a clear clue before guessing. That keeps a mix-up from turning into a bigger worry.",
        ),
        QAItem(
            question="Why is a pirate setting good for a misunderstanding story?",
            answer="Pirate stories often use maps, notes, and funny words, so a child can easily guess wrong at first. Then the grown-up can clear things up in a cheerful way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,R) :- setting(S), misunderstanding(M), response(R), sense(R,N), N >= 2.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP gate differs from Python gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        with redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as err:
        ok = False
        print(f"SMOKE TEST FAILED: {err}")
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="deck", misunderstanding="constipate", response="explain",
                        child="Mina", child_type="girl", helper="Pip", helper_type="boy",
                        adult="Captain Mara", adult_type="mother"),
            StoryParams(setting="cabin", misunderstanding="constipate", response="laugh",
                        child="Jasper", child_type="boy", helper="Rose", helper_type="girl",
                        adult="Captain Eli", adult_type="father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            i += 1
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    ms = world.facts["ms"]
    return [
        f'Write a pirate story for a 3-to-5-year-old that includes the word "{ms.word}" and begins with a misunderstanding.',
        f'Tell a gentle pirate tale where a child guesses what "{ms.word}" means, gets it wrong, and then learns the true meaning from a grown-up.',
        f'Write a small story with a misunderstanding on a ship and a calm correction that uses the word "{ms.word}".',
    ]


if __name__ == "__main__":
    main()
