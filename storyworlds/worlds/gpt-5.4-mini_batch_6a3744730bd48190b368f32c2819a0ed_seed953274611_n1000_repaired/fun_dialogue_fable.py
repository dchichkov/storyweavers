#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fun_dialogue_fable.py
======================================================

A small fable-style storyworld about a playful village, a bit of bragging, a
calm correction, and a kinder ending. It uses dialogue as the main narrative
instrument and keeps the story child-facing, concrete, and state-driven.

The core premise:
- A cheerful character wants fun right now.
- Another character warns that one kind of fun can spill into trouble.
- A small choice turns the moment from bragging into sharing.
- The ending shows fun made safer and kinder.

This world is intentionally tiny and self-contained.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    crowd: str
    mood: str
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
class Game:
    id: str
    label: str
    phrase: str
    danger: str
    safe: str
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
class Lesson:
    id: str
    warning: str
    wisdom: str
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
        clone = World()
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    actor = world.get("fox")
    if actor.memes["boast"] < THRESHOLD:
        return out
    if actor.meters["spilled"] >= THRESHOLD:
        return out
    sig = ("spill", actor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    actor.meters["spilled"] += 1
    world.get("berries").meters["scattered"] += 1
    world.get("field").meters["mess"] += 1
    for e in world.characters():
        e.memes["surprise"] += 1
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def fun_at_risk(game: Game, setting: Setting) -> bool:
    return "play" in setting.tags and "mess" in game.tags


def sensible_games() -> list[Game]:
    return [g for g in GAMES.values() if g.id in {"berries", "music"}]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for gid, game in GAMES.items():
            if fun_at_risk(game, setting):
                combos.append((sid, gid))
    return combos


@dataclass
class StoryParams:
    setting: str = ""
    game: str = ""
    fox: str = ""
    crow: str = ""
    elder: str = ""
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


def setup(world: World, params: StoryParams) -> None:
    setting = SETTINGS[params.setting]
    game = GAMES[params.game]
    fox = world.add(Entity(id=params.fox, kind="character", type="boy", role="boaster", traits=["lively"]))
    crow = world.add(Entity(id=params.crow, kind="character", type="girl", role="cautioner", traits=["wise"]))
    elder = world.add(Entity(id=params.elder, kind="character", type="woman", role="elder", label="the elder"))
    field = world.add(Entity(id="field", type="place", label=setting.place))
    berries = world.add(Entity(id="berries", type="thing", label="berries"))
    fox.memes["fun"] = 1
    fox.memes["want_fun"] = 1
    crow.memes["care"] = 1
    world.facts.update(setting=setting, game=game, fox=fox, crow=crow, elder=elder, field=field, berries=berries)


def tell(world: World, params: StoryParams) -> None:
    setting: Setting = world.facts["setting"]
    game: Game = world.facts["game"]
    fox: Entity = world.facts["fox"]
    crow: Entity = world.facts["crow"]
    elder: Entity = world.facts["elder"]
    berries: Entity = world.facts["berries"]

    world.say(
        f"In {setting.place}, {setting.detail}, and the morning felt bright and free."
    )
    world.say(
        f"{fox.id} grinned. \"I want {game.phrase},\" {fox.id} said. "
        f"\"It will be fun!\""
    )
    world.say(
        f"{crow.id} tilted {crow.pronoun('possessive')} head. \"Fun is sweet,\" "
        f"{crow.id} said, \"but not when it turns rough.\""
    )

    world.para()
    fox.memes["boast"] += 1
    fox.memes["desire"] += 1
    world.say(
        f"\"I can do it my way,\" {fox.id} said, and {fox.pronoun()} hurried ahead."
    )
    if params.game == "berries":
        world.say(
            f"{crow.id} called, \"Careful -- the berries on the bush are full and soft.\""
        )
    else:
        world.say(
            f"{crow.id} called, \"Careful -- the little drum can shake the whole lane.\""
        )

    propagate(world, narrate=False)

    world.para()
    if params.game == "berries":
        world.say(
            f"{fox.id} stopped, looked at the scattered berries, and blinked. "
            f"\"Oh. That was not kind fun,\" {fox.id} whispered."
        )
        world.say(
            f"{elder.label_word.capitalize()} smiled and said, \"You can still have fun, "
            f"little one. Try gathering the berries gently and sharing them.\""
        )
        fox.memes["shame"] += 1
        fox.memes["kindness"] += 1
        crow.memes["relief"] += 1
        world.say(
            f"{fox.id} and {crow.id} picked the berries together, and the red fruit "
            f"filled the basket instead of the dirt."
        )
        world.say(
            f"\"Fun is better when everyone can smile,\" {crow.id} said."
        )
    else:
        world.say(
            f"{fox.id} slowed down and listened. The little drum made a soft beat, "
            f"and no one was pushed or hurt."
        )
        world.say(
            f"{elder.label_word.capitalize()} said, \"Fun needs a gentle paw. Then it lasts.\""
        )
        fox.memes["kindness"] += 1
        crow.memes["joy"] += 1
        world.say(
            f"So {fox.id} played the drum softly while {crow.id} clapped, and the lane "
            f"kept its happy rhythm."
        )

    world.facts.update(
        outcome="shared_fun",
        spilled=fox.meters["spilled"] >= THRESHOLD,
        changed=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    game: Game = f["game"]
    return [
        f'Write a short fable for a young child that includes the word "fun" and the line "{game.safe}".',
        f"Tell a dialogue-driven fable where {f['fox'].id} wants {game.phrase}, but {f['crow'].id} warns about keeping fun gentle.",
        "Write a simple moral story with talking animals, a small mistake, and a kinder way to keep the fun going.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fox: Entity = f["fox"]
    crow: Entity = f["crow"]
    elder: Entity = f["elder"]
    game: Game = f["game"]
    items = [
        QAItem(
            question="What did the fox want to do?",
            answer=f"{fox.id} wanted {game.phrase}. {fox.id} thought it would be fun, even before listening carefully."
        ),
        QAItem(
            question="What did the crow warn about?",
            answer=f"{crow.id} warned that fun can turn rough if the action is too wild. {crow.id} wanted the play to stay gentle and safe."
        ),
        QAItem(
            question="What did the elder teach?",
            answer=f"{elder.label_word.capitalize()} said that fun is better when it is kind and shared. The elder's advice turned the moment from bragging into better play."
        ),
    ]
    if f.get("spilled"):
        items.append(
            QAItem(
                question="What changed after the fox hurried ahead?",
                answer="The berries were scattered on the ground, so the fox saw that boasting caused a messy problem. After that, the fox chose a gentler kind of fun."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    game: Game = f["game"]
    out: list[QAItem] = []
    for topic in sorted(game.tags):
        if topic in KNOWLEDGE:
            q, a = KNOWLEDGE[topic]
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "orchard": Setting(id="orchard", place="the orchard", detail="the apple trees leaned over the grass", crowd="the path", mood="bright", tags={"play", "peace"}),
    "meadow": Setting(id="meadow", place="the meadow", detail="wildflowers bent in the breeze", crowd="the hill", mood="open", tags={"play", "peace"}),
}

GAMES = {
    "berries": Game(id="berries", label="berries", phrase="a game of berry-picking", danger="the berries would spill", safe="pick the berries gently", tags={"mess", "berries"}),
    "music": Game(id="music", label="drum", phrase="a loud drum game", danger="the beat might startle the hens", safe="play the drum softly", tags={"music", "sound"}),
}

KNOWLEDGE = {
    "berries": ("What are berries?", "Berries are small fruits that can be picked carefully and shared with others."),
    "music": ("What is music?", "Music is made with sounds and rhythms, and it can be loud or soft."),
    "mess": ("Why should we be careful with a messy game?", "A messy game can scatter things, so gentle play helps keep the place tidy and safe."),
    "sound": ("What is a gentle sound?", "A gentle sound is soft enough not to scare or hurt anyone."),
}

CURATED = [
    StoryParams(setting="orchard", game="berries", fox="Fenn", crow="Clea", elder="Aunt Reed"),
    StoryParams(setting="meadow", game="music", fox="Milo", crow="Rin", elder="Old Moss"),
]


def explain_rejection(setting: Setting, game: Game) -> str:
    return f"(No story: {game.phrase} does not fit this little fable here.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("(No story: unknown setting.)")
    if args.game and args.game not in GAMES:
        raise StoryError("(No story: unknown game.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.game is None or c[1] == args.game)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, game = rng.choice(sorted(combos))
    fox = rng.choice(["Fenn", "Milo", "Pip", "Lark", "Tavi"])
    crow = rng.choice(["Clea", "Rin", "Nell", "Suri", "Wren"])
    if crow == fox:
        crow = "Wren"
    elder = rng.choice(["Aunt Reed", "Old Moss", "Grand Birch"])
    return StoryParams(setting=setting, game=game, fox=fox, crow=crow, elder=elder)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.game not in GAMES:
        raise StoryError("(No story: invalid params.)")
    world = World()
    setup(world, params)
    tell(world, params)
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
fun_at_risk(S,G) :- setting(S), game(G), play(S), mess_game(G).
valid(S,G) :- fun_at_risk(S,G).
outcome(shared_fun) :- valid(S,G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tag in s.tags:
            lines.append(asp.fact(tag, sid))
    for gid, g in GAMES.items():
        lines.append(asp.fact("game", gid))
        for tag in g.tags:
            lines.append(asp.fact(f"{tag}_game", gid))
        if "mess" in g.tags:
            lines.append(asp.fact("mess_game", gid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"MISMATCH: smoke test failed: {exc}")
        rc = 1
    else:
        print("OK: ASP parity and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny dialogue fable world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--game", choices=GAMES)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, g in combos:
            print(f"  {s:8} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
