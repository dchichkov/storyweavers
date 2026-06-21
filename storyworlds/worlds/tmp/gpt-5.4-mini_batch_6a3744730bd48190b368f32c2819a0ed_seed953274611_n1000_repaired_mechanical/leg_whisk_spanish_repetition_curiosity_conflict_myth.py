#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/leg_whisk_spanish_repetition_curiosity_conflict_myth.py
========================================================================================

A tiny mythic storyworld about a child at a shrine, a whispered instruction in
Spanish, a whisk that stirs a blessing, and a repeated rule that must be
understood before the end.

The world is built around:
- repetition as an incantation / ritual beat
- curiosity as the reason the child asks again
- conflict as the moment the child wants to cross a sacred boundary
- mythic style with concrete, child-facing imagery

The required seed words are woven through the model and the stories:
leg, whisk, spanish.

Run:
    python storyworlds/worlds/gpt-5.4-mini/leg_whisk_spanish_repetition_curiosity_conflict_myth.py
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    shrine: str
    child_name: str
    child_gender: str
    keeper_name: str
    keeper_gender: str
    whisk: str
    spanish_word: str
    repeated_rule: str
    conflict_threshold: int
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


@dataclass
class World:
    shrine: str
    child: Entity
    keeper: Entity
    whisk: Entity
    bell: Entity
    stone: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        return World(
            shrine=self.shrine,
            child=_copy.deepcopy(self.child),
            keeper=_copy.deepcopy(self.keeper),
            whisk=_copy.deepcopy(self.whisk),
            bell=_copy.deepcopy(self.bell),
            stone=_copy.deepcopy(self.stone),
            facts=dict(self.facts),
            paragraphs=[[]],
        )
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


SHRINES = {
    "moonwell": {
        "name": "the moonwell",
        "image": "a silver well that held the moon like a coin in water",
        "keeper": "keeper of the well",
        "ending": "the moonwell shone again, quiet and kind",
    },
    "sun-temple": {
        "name": "the sun-temple",
        "image": "a bright temple with gold steps and painted birds",
        "keeper": "keeper of the temple",
        "ending": "the sun-temple glowed softly, like a warm lantern",
    },
    "river-shrine": {
        "name": "the river-shrine",
        "image": "a stone shrine beside a whispering river",
        "keeper": "keeper of the shrine",
        "ending": "the river-shrine kept singing beside the water",
    },
}

WHISKS = {
    "feather_whisk": {
        "label": "feather whisk",
        "phrase": "a feather whisk",
        "use": "stir the blessing",
        "sound": "shh-shh",
        "kind": "tool",
    },
    "copper_whisk": {
        "label": "copper whisk",
        "phrase": "a copper whisk",
        "use": "wake the old bells",
        "sound": "cling-cling",
        "kind": "tool",
    },
}

SPANISH_WORDS = {
    "espera": "espera",
    "calma": "calma",
    "suave": "suave",
}

REPEATED_RULES = {
    "no_touch_water": "No touch the moonwell water.",
    "no_cross_line": "Stay behind the chalk line.",
    "no_ring_bell": "Do not ring the old bell alone.",
}

CURATED = [
    StoryParams(
        shrine="moonwell",
        child_name="Lina",
        child_gender="girl",
        keeper_name="Abuela",
        keeper_gender="mother",
        whisk="feather_whisk",
        spanish_word="espera",
        repeated_rule="no_cross_line",
        conflict_threshold=2,
        seed=7,
    ),
    StoryParams(
        shrine="sun-temple",
        child_name="Nico",
        child_gender="boy",
        keeper_name="Tia",
        keeper_gender="mother",
        whisk="copper_whisk",
        spanish_word="calma",
        repeated_rule="no_ring_bell",
        conflict_threshold=2,
        seed=11,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about curiosity, repetition, and a sacred warning.")
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--whisk", choices=WHISKS)
    ap.add_argument("--spanish-word", choices=SPANISH_WORDS)
    ap.add_argument("--rule", choices=REPEATED_RULES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper-name")
    ap.add_argument("--keeper-gender", choices=["mother", "father", "woman", "man"])
    ap.add_argument("--threshold", type=int, choices=[1, 2, 3])
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
    shrine = args.shrine or rng.choice(sorted(SHRINES))
    whisk = args.whisk or rng.choice(sorted(WHISKS))
    spanish_word = args.spanish_word or rng.choice(sorted(SPANISH_WORDS))
    rule = args.rule or rng.choice(sorted(REPEATED_RULES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    keeper_gender = args.keeper_gender or rng.choice(["mother", "father", "woman", "man"])
    child_name = args.child_name or rng.choice(["Lina", "Nico", "Mara", "Pablo", "Iris", "Tomas"])
    keeper_name = args.keeper_name or rng.choice(["Abuela", "Tia", "Mama", "Papa", "Señora Sol"])
    threshold = args.threshold if args.threshold is not None else rng.choice([1, 2, 2, 3])

    if args.spanish_word and args.spanish_word not in SPANISH_WORDS:
        raise StoryError("Unknown Spanish word.")
    return StoryParams(
        shrine=shrine,
        child_name=child_name,
        child_gender=child_gender,
        keeper_name=keeper_name,
        keeper_gender=keeper_gender,
        whisk=whisk,
        spanish_word=spanish_word,
        repeated_rule=rule,
        conflict_threshold=threshold,
        seed=None,
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for shrine in SHRINES:
        for whisk in WHISKS:
            for rule in REPEATED_RULES:
                combos.append((shrine, whisk, rule))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for s in SHRINES:
        lines.append(asp.fact("shrine", s))
    for w in WHISKS:
        lines.append(asp.fact("whisk", w))
    for r in REPEATED_RULES:
        lines.append(asp.fact("rule", r))
    for word in SPANISH_WORDS:
        lines.append(asp.fact("spanish_word", word))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,W,R) :- shrine(S), whisk(W), rule(R).
curious(X) :- asks_again(X).
conflict(X) :- curious(X), crosses_line(X).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP valid-combo gates.")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and story-generation smoke test passed.")
    return 0


def pronoun_type(gender: str) -> str:
    return {"girl": "girl", "boy": "boy", "mother": "mother", "father": "father", "woman": "woman", "man": "man"}[gender]


def make_world(params: StoryParams) -> World:
    shrine_cfg = SHRINES[params.shrine]
    whisk_cfg = WHISKS[params.whisk]
    child = Entity(id=params.child_name, kind="character", type=params.child_gender, role="curious child")
    keeper = Entity(id=params.keeper_name, kind="character", type=params.keeper_gender, role="keeper")
    whisk = Entity(id=whisk_cfg["label"], kind="thing", type="tool", label=whisk_cfg["label"], tags={"whisk"})
    bell = Entity(id="bell", kind="thing", type="thing", label="old bell", tags={"bell"}, meters={"ringing": 0.0})
    stone = Entity(id="stone", kind="thing", type="thing", label="chalk line stone", tags={"stone"})
    world = World(shrine=shrine_cfg["name"], child=child, keeper=keeper, whisk=whisk, bell=bell, stone=stone)
    world.facts.update(shrine_cfg=shrine_cfg, whisk_cfg=whisk_cfg)
    return world


def tell(world: World, params: StoryParams) -> None:
    shrine_cfg = SHRINES[params.shrine]
    whisk_cfg = WHISKS[params.whisk]
    child = world.child
    keeper = world.keeper

    child.memes["curiosity"] = 1.0
    keeper.memes["warning"] = 1.0

    world.say(
        f"Long ago, at {shrine_cfg['name']}, there was a place that looked like a dream: {shrine_cfg['image']}."
    )
    world.say(
        f"There {child.id} came with {keeper.id}, and {keeper.id} said the same rule twice: "
        f'"{REPEATED_RULES[params.repeated_rule]}"'
    )
    world.say(
        f'"{REPEATED_RULES[params.repeated_rule]}" {keeper.id} said again, because old places remember more when words are repeated.'
    )

    world.para()
    world.say(
        f"But {child.id} was full of curiosity. {child.id} leaned on one {child.pronoun("object")} {child.pronoun("object")} {child.pronoun("possessive")} leg and asked, '
        f'"Why do you say it twice?"'
    )
    world.say(
        f'The keeper answered in Spanish, "{params.spanish_word}." Then {keeper.id} said it again in Spanish: "{params.spanish_word}."'
    )

    child.memes["curiosity"] += 1
    if params.conflict_threshold <= 2:
        child.memes["conflict"] += 1

    world.say(
        f"{child.id} wanted to know more and more. {child.id} reached for {whisk_cfg['phrase']} to {whisk_cfg['use']}, "
        f"just to see if the rule really mattered."
    )

    world.para()
    world.say(
        f"{keeper.id} stepped close and repeated the rule a third time: "
        f'"{REPEATED_RULES[params.repeated_rule]}"'
    )
    world.say(
        f"The words sounded like a drumbeat. Repeated once, they warned. Repeated twice, they warned harder. Repeated thrice, they became a wall."
    )

    if params.repeated_rule == "no_cross_line":
        world.say(
            f"{child.id} stopped with one foot near the chalk line and one leg behind it."
        )
    elif params.repeated_rule == "no_ring_bell":
        world.say(
            f"{child.id} looked at the bell and felt the tug of conflict, because the bell wanted to sing and the keeper wanted quiet."
        )
    else:
        world.say(
            f"{child.id} looked at the water and felt curiosity turn into conflict, because the shrine asked for patience."
        )

    world.para()
    if child.memes.get("conflict", 0.0) >= THRESHOLD:
        world.say(
            f"{child.id} almost disobeyed, but then {child.id} heard the Spanish word again: {params.spanish_word}."
        )
        world.say(
            f"It meant wait, or be still, or listen—at least in the way the keeper spoke it, with a hand on the child’s shoulder."
        )
        world.say(
            f"{child.id} breathed out, put down {whisk_cfg['phrase']}, and let the rule stay unbroken."
        )
        world.say(
            f"Then {keeper.id} smiled and let {child.id} help stir the blessing with the whisk, but only from the safe side of the line."
        )
    else:
        world.say(
            f"{child.id} listened at once and stayed back, so the shrine kept its calm without any hard struggle."
        )
        world.say(
            f"Together they used {whisk_cfg['phrase']} to {whisk_cfg['use']} from the safe side, and the bells stayed asleep."
        )

    world.para()
    world.say(
        f"In the end, the old place was not angry. It simply became brighter because the child had learned that a repeated rule can be a kind of love."
    )
    world.say(
        f"And so {shrine_cfg['ending']}, while {child.id} walked away with the word {params.spanish_word} still ringing in {child.pronoun('possessive')} ears."
    )

    world.facts.update(
        child=child,
        keeper=keeper,
        whisk=whisk,
        bell=bell,
        stone=stone,
        repeated_rule=params.repeated_rule,
        spanish_word=params.spanish_word,
        outcome="resolved",
    )


def story_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f"Write a mythic story that includes the words leg, whisk, and spanish, and centers on repetition, curiosity, and conflict.",
        f"Tell a child-sized myth about {p['child'].id} at {p['shrine_cfg']['name']} where a rule is repeated until it matters.",
        f"Write a gentle legend in which {p['child'].id} hears a Spanish word, wants to know why, and chooses to listen instead of crossing the line.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    child = p["child"]
    keeper = p["keeper"]
    return [
        QAItem(
            question=f"Why did {child.id} keep asking questions?",
            answer=f"{child.id} was curious, so {child.id} asked again and again until the meaning of the repeated rule felt clear. The curiosity made the conflict bigger, but it also helped {child.id} learn why the warning mattered."
        ),
        QAItem(
            question="What was repeated in the story?",
            answer=f"The keeper repeated {REPEATED_RULES[p['repeated_rule']]} more than once, like an old spell that becomes stronger when spoken again. Each repetition turned the warning into something the child could not ignore."
        ),
        QAItem(
            question=f"How did the Spanish word change the story?",
            answer=f"The Spanish word {p['spanish_word']} gave the warning a strange, sacred sound. It slowed the child down and helped {child.id} understand that the keeper was asking for patience, not just making noise."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whisk?",
            answer="A whisk is a tool with wires or feathers that can stir or mix things. In this world, the whisk also feels like a ritual tool because it helps the blessing move."
        ),
        QAItem(
            question="What does repetition do in a myth?",
            answer="Repetition makes a word or rule feel important, almost like a chant. When something is repeated, people remember it more easily and may treat it like a sacred truth."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know why something is true. It can lead to learning, but it can also lead to trouble if someone tests a rule before they understand it."
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.shrine not in SHRINES or params.whisk not in WHISKS or params.repeated_rule not in REPEATED_RULES:
        raise StoryError("Invalid story parameters.")
    world = make_world(params)
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        print(sample.world.facts)
    if qa:
        print()
        for group, items in [("Prompts", sample.prompts), ("Story Q&A", sample.story_qa), ("World Q&A", sample.world_qa)]:
            print(f"== {group} ==")
            for item in items:
                if isinstance(item, QAItem):
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
                else:
                    print(item)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible combos:")
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
