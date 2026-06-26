#!/usr/bin/env python3
"""
A small adventure-style friendship storyworld about a prank idea and a playful persona.

This world generates a complete, state-driven tale about two friends on a small
adventure. One of them gets a prank idea, they try on a new persona, and the
friendship decides whether the prank stays kind.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    trail: str
    afford: set[str]


@dataclass
class Idea:
    id: str
    name: str
    prank: str
    setup: str
    reveal: str
    risk: str
    keyword: str = "prank"


@dataclass
class Persona:
    id: str
    name: str
    costume: str
    manner: str
    reveal: str
    covers: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    idea: str
    persona: str
    hero: str
    friend: str
    hero_type: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(place="the forest path", trail="the mossy trail", afford={"prank", "hide"}),
    "harbor": Setting(place="the harbor docks", trail="the wooden pier", afford={"prank", "hide"}),
    "fair": Setting(place="the lantern fair", trail="the bright midway", afford={"prank", "hide"}),
    "cave": Setting(place="the crystal cave", trail="the echoing tunnel", afford={"hide"}),
}

IDEAS = {
    "signs": Idea(
        id="signs",
        name="swap the trail signs",
        prank="prank",
        setup="move the tiny trail signs and make the path look extra mysterious",
        reveal="the signs were all back where they belonged",
        risk="it might confuse a lost traveler",
    ),
    "lantern": Idea(
        id="lantern",
        name="hide the lantern bundle",
        prank="prank",
        setup="hide the lantern bundle and leave a silly clue trail",
        reveal="the lanterns glowed from a higher branch",
        risk="someone could trip in the dark",
    ),
    "echo": Idea(
        id="echo",
        name="make a funny echo game",
        prank="prank",
        setup="whisper strange explorer words and pretend the cave was talking back",
        reveal="the cave echoed every silly word",
        risk="the joke might feel spooky",
    ),
}

PERSONAS = {
    "explorer": Persona(
        id="explorer",
        name="secret explorer persona",
        costume="a wide-brimmed hat and a paper badge",
        manner="speak in dramatic whispers and point at every clue",
        reveal="the badge slipped and showed the truth",
        covers={"head"},
    ),
    "pirate": Persona(
        id="pirate",
        name="playful pirate persona",
        costume="a striped scarf and a toy telescope",
        manner="talk like a bold sea captain",
        reveal="the scarf came loose and everyone laughed",
        covers={"head"},
    ),
    "ghost": Persona(
        id="ghost",
        name="pretend ghost persona",
        costume="a white sheet with two careful eye holes",
        manner="float slowly and say boo in a tiny voice",
        reveal="the sheet snagged on a branch",
        covers={"whole"},
    ),
}


NAMES = {
    "girl": ["Mia", "Lena", "Nora", "Zoe", "Ivy"],
    "boy": ["Theo", "Ben", "Finn", "Max", "Leo"],
}
TRAITS = ["brave", "curious", "lively", "gentle", "bold"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: Setting, idea: Idea, persona: Persona) -> bool:
    if idea.id == "echo" and setting.place != "the crystal cave":
        return False
    if idea.id == "lantern" and setting.place not in {"the forest path", "the lantern fair", "the harbor docks"}:
        return False
    if persona.id == "ghost" and setting.place == "the lantern fair":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, s in SETTINGS.items():
        for i_id, i in IDEAS.items():
            for p_id, p in PERSONAS.items():
                if valid_combo(s, i, p):
                    out.append((s_id, i_id, p_id))
    return out


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def tell(setting: Setting, idea: Idea, persona: Persona, hero: Entity, friend: Entity) -> World:
    world = World(setting)
    world.add(hero)
    world.add(friend)

    hero.memes["curiosity"] = 1
    friend.memes["loyalty"] = 1

    world.say(
        f"{hero.id} and {friend.id} were best friends, always ready for a small adventure "
        f"along {setting.trail}."
    )
    world.say(
        f"On that bright morning, {hero.id} got an idea: {idea.name}."
    )
    world.say(
        f"The idea was a harmless {idea.prank} at {setting.place}, just enough to make "
        f"their walk feel like a mystery."
    )

    world.para()
    world.say(
        f"To make it feel grand, {hero.id} tried on a {persona.name}. "
        f"{hero.pronoun().capitalize()} wore {persona.costume} and started to {persona.manner}."
    )
    world.say(
        f"{friend.id} grinned at first, because the two of them loved turning an ordinary day "
        f"into a little adventure."
    )

    hero.memes["playfulness"] = 1
    friend.memes["joy"] = 1

    if idea.id == "signs":
        world.say(
            f"They began to {idea.setup}, and soon the trail looked like a secret quest."
        )
    elif idea.id == "lantern":
        world.say(
            f"They began to {idea.setup}, and the path filled with tiny, curious shadows."
        )
    else:
        world.say(
            f"They began to {idea.setup}, and every soft sound bounced back as if the cave were listening."
        )

    world.para()
    world.say(
        f"Then {friend.id} noticed the risk. {idea.risk.capitalize()}, and it might stop the adventure "
        f"from feeling kind."
    )
    friend.memes["worry"] = 1
    hero.memes["guilt"] = 1

    world.say(
        f"{friend.id} said that a prank should make people laugh, not feel tricked for real."
    )
    world.say(
        f"{hero.id} looked at the {persona.name} and realized the best idea was the one that kept "
        f"their friendship bright."
    )

    world.para()
    world.say(
        f"So they changed the prank idea. Instead of leaving anyone confused, they made the reveal part of the fun: "
        f"{idea.reveal}."
    )
    world.say(
        f"{hero.id} took off the {persona.name}, and {persona.reveal}."
    )
    world.say(
        f"{friend.id} laughed, relieved, and the two friends finished their adventure side by side."
    )

    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["guilt"] = 0
    friend.memes["worry"] = 0
    friend.memes["trust"] = 1
    hero.memes["trust"] = 1

    world.facts.update(
        hero=hero,
        friend=friend,
        setting=setting,
        idea=idea,
        persona=persona,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a young child that includes the words "prank", "idea", and "persona".',
        f"Tell a friendship story where {f['hero'].id} and {f['friend'].id} go on a small adventure at {f['setting'].place} and must decide whether a prank stays kind.",
        f"Write a gentle story with a playful persona, a prank idea, and a happy ending about two best friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    setting: Setting = f["setting"]
    idea: Idea = f["idea"]
    persona: Persona = f["persona"]

    return [
        QAItem(
            question=f"Who were the story's main friends at {setting.place}?",
            answer=f"The story was about {hero.id} and {friend.id}, two best friends on a small adventure at {setting.place}.",
        ),
        QAItem(
            question=f"What prank idea did {hero.id} have?",
            answer=f"{hero.id} had the idea to {idea.name}, which was a playful prank for the adventure.",
        ),
        QAItem(
            question=f"What persona did {hero.id} try on?",
            answer=f"{hero.id} tried on a {persona.name} with {persona.costume}, so the walk would feel mysterious.",
        ),
        QAItem(
            question=f"Why did the friends change the prank idea?",
            answer=(
                f"They changed it because {friend.id} noticed it could stop being kind. "
                f"They wanted the prank to make people laugh, not feel tricked for real."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with the friends choosing a safer, funnier reveal, taking off the persona, "
                f"and finishing the adventure laughing together."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a prank?",
            answer="A prank is a playful joke or trick, but a good prank should be harmless and kind.",
        ),
        QAItem(
            question="What is an idea?",
            answer="An idea is a thought about something you might do or make.",
        ),
        QAItem(
            question="What is a persona?",
            answer="A persona is a role or manner someone pretends to have, like acting mysterious or bold.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about another person, listening to them, and trying to do things together kindly.",
        ),
        QAItem(
            question="What makes an adventure feel exciting?",
            answer="An adventure feels exciting when friends go somewhere new, notice clues, and solve small problems along the way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_combo(S,I,P) :- setting(S), idea(I), persona(P), okay(S,I,P).

#show valid_combo/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s_id in SETTINGS:
        lines.append(asp.fact("setting", s_id))
    for i_id in IDEAS:
        lines.append(asp.fact("idea", i_id))
    for p_id in PERSONAS:
        lines.append(asp.fact("persona", p_id))
    for s_id, i_id, p_id in valid_combos():
        lines.append(asp.fact("okay", s_id, i_id, p_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure-style friendship prank storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--idea", choices=IDEAS)
    ap.add_argument("--persona", choices=PERSONAS)
    ap.add_argument("--hero", choices=[n for names in NAMES.values() for n in names])
    ap.add_argument("--friend", choices=[n for names in NAMES.values() for n in names])
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.setting or args.idea or args.persona:
        combos = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.idea is None or c[1] == args.idea)
            and (args.persona is None or c[2] == args.persona)
        ]
    if not combos:
        raise StoryError("No valid adventure fits those choices.")

    setting, idea, persona = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES[hero_type])
    friend = args.friend or rng.choice([n for n in NAMES[friend_type] if n != hero] or NAMES[friend_type])
    if hero == friend:
        raise StoryError("The two friends must be different characters.")

    return StoryParams(
        setting=setting,
        idea=idea,
        persona=persona,
        hero=hero,
        friend=friend,
        hero_type=hero_type,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    idea = IDEAS[params.idea]
    persona = PERSONAS[params.persona]

    hero = Entity(id=params.hero, kind="character", type=params.hero_type)
    friend = Entity(id=params.friend, kind="character", type=params.friend_type)

    world = tell(setting, idea, persona, hero, friend)
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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid adventure combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for s in sorted(SETTINGS):
            for i in sorted(IDEAS):
                for p in sorted(PERSONAS):
                    if valid_combo(SETTINGS[s], IDEAS[i], PERSONAS[p]):
                        params = StoryParams(
                            setting=s,
                            idea=i,
                            persona=p,
                            hero=NAMES["girl"][0],
                            friend=NAMES["boy"][0],
                            hero_type="girl",
                            friend_type="boy",
                        )
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(1000, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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


if __name__ == "__main__":
    main()
