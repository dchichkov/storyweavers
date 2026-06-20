#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/make_gerund_moral_value_lesson_learned_foreshadowing.py
========================================================================================

A standalone tiny storyworld for a rhyming classroom craft tale about
making -ing words, using a warm moral, a clear lesson learned, and light
foreshadowing.

The world model tracks children, a teacher, paper cards, glue, and a poster.
The tension comes from a small craft mistake: the glue pot is left open, a drip
starts, and the child must choose whether to hide the mess or tell the teacher.
The resolution is a simple, child-facing fix: honesty, help, and careful
cleanup. The story ends with the finished gerund poster and a small moral.

Supported CLI:
- default generation
- -n / --all / --seed / --trace / --qa / --json
- --asp / --verify / --show-asp
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Word:
    id: str
    base: str
    gerund: str
    rhyme: str
    meaning: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Craft:
    id: str
    label: str
    phrase: str
    danger: str
    fix: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    pot = world.get("glue_pot")
    if pot.meters["open"] < THRESHOLD:
        return out
    if pot.meters["drip"] >= THRESHOLD and ("spill",) not in world.fired:
        world.fired.add(("spill",))
        world.get("table").meters["sticky"] += 1
        world.get("poster").meters["smudged"] += 1
        world.get("kid").memes["worry"] += 1
        out.append("__drip__")
    return out


def _r_honesty(world: World) -> list[str]:
    kid = world.get("kid")
    if kid.memes["honesty"] < THRESHOLD or ("honest",) in world.fired:
        return []
    if world.get("poster").meters["smudged"] < THRESHOLD:
        return []
    world.fired.add(("honest",))
    world.get("teacher").memes["trust"] += 1
    return ["__truth__"]


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("honesty", "social", _r_honesty)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def rhyme_line(a: str, b: str) -> str:
    return f"{a} / {b}"


def predict_spill(world: World) -> dict:
    sim = world.copy()
    sim.get("glue_pot").meters["open"] = 1
    sim.get("glue_pot").meters["drip"] = 1
    propagate(sim, narrate=False)
    return {"smudged": sim.get("poster").meters["smudged"] >= THRESHOLD}


def _do_mistake(world: World) -> None:
    world.get("glue_pot").meters["open"] = 1
    world.get("glue_pot").meters["drip"] = 1
    propagate(world, narrate=False)


def tell(world: World, kid_name: str, kid_gender: str, teacher_gender: str, word: Word, craft: Craft) -> World:
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="learner"))
    teacher = world.add(Entity(id="Teacher", kind="character", type=teacher_gender, role="teacher", label="the teacher"))
    world.add(Entity(id="desk", label="the desk"))
    world.add(Entity(id="glue_pot", label="the glue pot"))
    world.add(Entity(id="poster", label="the poster"))
    world.add(Entity(id="cards", label="the word cards"))

    kid.memes["curious"] += 1
    kid.memes["honesty"] += 1
    world.say(
        f"At class one bright day, {kid.id} sat in a row, "
        f"with word cards in hand and a grin in tow."
    )
    world.say(
        f'{kid.id} wished to make-gerund magic and make words sing, '
        f"to turn {word.base} into {word.gerund}, a shiny new thing."
    )
    world.say(
        f"{teacher.label_word.capitalize()} smiled and showed a first clue near: "
        f"'{word.base} can bloom into {word.gerund}, my dear.'"
    )

    world.para()
    world.say(
        f"But the glue pot was open, and that was a poor plan; "
        f"a tiny wet drip slid down like a tiny old fan."
    )
    world.say(
        f"That was the foreshadowing, small as a seed: "
        f"the sticky little drip would soon make mischief indeed."
    )

    _do_mistake(world)
    if predict_spill(world)["smudged"]:
        kid.memes["worry"] += 1

    world.para()
    world.say(
        f"{kid.id} saw the smudge on the poster and felt a soft pinch; "
        f"{kid.pronoun().capitalize()} could hide it, or tell, and the choice was the clinch."
    )

    kid.memes["honesty"] += 1
    world.get("glue_pot").meters["open"] = 0
    world.get("glue_pot").meters["drip"] = 0
    world.say(
        f'{" " if False else ""}{kid.id} told {teacher.pronoun("object")} right away, with a brave little glow, '
        f'"I made a sticky mess, and I want to help fix it, so."'
    )
    propagate(world, narrate=False)
    world.say(
        f"{teacher.label_word.capitalize()} nodded and laughed a kind, warm sound; "
        f"together they wiped the desk clean all around."
    )
    world.say(
        f"The cards stayed tidy, the poster looked neat, and the class could keep "
        f"its little rhyme-beat."
    )

    world.para()
    world.say(
        f"{kid.id} finished the chart with a cheerful hand, "
        f"writing {word.gerund} beside {word.rhyme} so the rule would stand."
    )
    world.say(
        f"The lesson learned was simple and bright: "
        f"honesty helps, and careful steps keep work just right."
    )

    world.facts.update(
        kid=kid, teacher=teacher, word=word, craft=craft,
        foreshadowed=True, smudged=world.get("poster").meters["smudged"] >= THRESHOLD,
        honest=True, fixed=True
    )
    return world


WORDS = {
    "make-gerund": Word("make-gerund", "make", "making", "rhyme", "to create by adding -ing", {"grammar", "make-gerund"}),
    "write-gerund": Word("write-gerund", "write", "writing", "light", "to form an action word", {"grammar"}),
    "smile-gerund": Word("smile-gerund", "smile", "smiling", "mile", "to make a word for doing", {"grammar"}),
}

CRAFTS = {
    "poster": Craft("poster", "class poster", "a class poster", "sticky smudges", "cleaning with a cloth", {"poster"}),
    "card": Craft("card", "word card", "a word card", "ink blots", "drying the card", {"card"}),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora"]
BOY_NAMES = ["Leo", "Max", "Sam", "Eli", "Theo"]


@dataclass
@dataclass
class StoryParams:
    word: str
    craft: str
    name: str
    gender: str
    teacher_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(w, c) for w in WORDS for c in CRAFTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming grammar-craft storyworld.")
    ap.add_argument("--word", choices=WORDS)
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-gender", choices=["woman", "man", "teacher"])
    ap.add_argument("--name")
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
    word = args.word or rng.choice(sorted(WORDS))
    craft = args.craft or rng.choice(sorted(CRAFTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    teacher_gender = args.teacher_gender or rng.choice(["woman", "man", "teacher"])
    return StoryParams(word, craft, name, gender, teacher_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming classroom story for a small child that includes the word "{f["word"].id}".',
        f"Tell a gentle story about {f['kid'].id} learning to make-gerund words with cards and a poster.",
        f'Write a moral story with foreshadowing, a small mistake, and a lesson learned about honesty and careful work.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, teacher, word = f["kid"], f["teacher"], f["word"]
    return [
        QAItem(
            question="What was the child trying to do?",
            answer=f"{kid.id} was trying to make-gerund words for a class poster. {kid.id} wanted to turn {word.base} into {word.gerund} and make the chart look bright."
        ),
        QAItem(
            question="What showed that trouble might happen soon?",
            answer="The open glue pot and the tiny drip were the foreshadowing. They hinted that the poster might get sticky before the child noticed."
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer="The child learned that honesty is kind and useful. Telling the teacher right away helped fix the mess quickly, and careful steps kept the work neat."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gerund?",
            answer="A gerund is a word made from a verb that ends in -ing, like making or smiling. It names an action as a thing you can talk about."
        ),
        QAItem(
            question="Why do teachers use posters in class?",
            answer="Teachers use posters to show ideas clearly and help everyone remember the lesson. A poster can make a new rule or word easy to see."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:10} ({e.type:7}) meters={dict(meters)} memes={dict(memes)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


CURATED = [
    StoryParams("make-gerund", "poster", "Mia", "girl", "woman"),
    StoryParams("write-gerund", "card", "Leo", "boy", "teacher"),
]


def generate(params: StoryParams) -> StorySample:
    world = World()
    w = WORDS[params.word]
    c = CRAFTS[params.craft]
    tell(world, params.name, params.gender, params.teacher_gender, w, c)
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


ASP_RULES = r"""
open_glue(P) :- glue_pot(P), open(P).
drip_risk(P) :- open_glue(P), drip(P).
smudge(Poster) :- poster(Poster), drip_risk(_).
honest(K) :- kid(K), truth(K).
lesson_learned(K) :- honest(K), teacher(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for w in WORDS:
        lines.append(asp.fact("word", w))
    for c in CRAFTS:
        lines.append(asp.fact("craft", c))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show word/1."))
    words = set(asp.atoms(model, "word"))
    if words != set((w,) for w in WORDS):
        print("MISMATCH in ASP facts")
        return 1
    print("OK: ASP facts present.")
    try:
        _ = generate(CURATED[0])
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:
        print(f"FAIL: generate crashed: {exc}")
        return 1
    return 0


def asp_list() -> None:
    import asp
    model = asp.one_model(asp_program("#show word/1.\n#show craft/1."))
    print("words:", ", ".join(sorted(w for (w,) in asp.atoms(model, "word"))))
    print("crafts:", ", ".join(sorted(c for (c,) in asp.atoms(model, "craft"))))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show word/1.\n#show craft/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
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
