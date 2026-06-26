#!/usr/bin/env python3
"""
A standalone storyworld for a small superhero story domain.

Seed sketch:
A young hero and a best friend share a quiet day in the city. The friend is
building a small plasticene model and carrying ramen for lunch when a rude
variant of the city's troublemaker snatches the bowl and mocks the model. The
hero has to choose between showing off power and protecting friendship. A
careful, brave move resolves the conflict, and the friend sees that real heroism
means helping, not boasting.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
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
    place: str = "the city square"
    backdrop: str = "bright towers and long sidewalks"


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    risk: str
    protected_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    villain_variant: str
    tool: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "city": Setting(place="the city square", backdrop="bright towers and busy roads"),
    "rooftop": Setting(place="the rooftop", backdrop="windy rails and glowing windows"),
    "park": Setting(place="the park", backdrop="trees, benches, and a clear blue sky"),
}

HEROES = {
    "spark": ("Spark", "boy", "small hero"),
    "nova": ("Nova", "girl", "brave hero"),
    "comet": ("Comet", "boy", "quick hero"),
    "glimmer": ("Glimmer", "girl", "kind hero"),
}

FRIENDS = {
    "milo": ("Milo", "boy", "best friend"),
    "mina": ("Mina", "girl", "best friend"),
    "tess": ("Tess", "girl", "best friend"),
    "leo": ("Leo", "boy", "best friend"),
}

VILLAINS = {
    "variant": ("Variant", "troublemaker", "rude rival"),
    "mirror_variant": ("Mirror Variant", "troublemaker", "copycat rival"),
}

TOOLS = {
    "plasticene": Tool(
        id="plasticene",
        label="plasticene",
        phrase="a little plasticene model",
        kind="model",
        risk="squished",
        protected_by="careful hands",
    ),
    "ramen": Tool(
        id="ramen",
        label="ramen",
        phrase="a warm bowl of ramen",
        kind="food",
        risk="spilled",
        protected_by="steady hands",
    ),
}

TRAITS = ["brave", "gentle", "quick-thinking", "cheerful", "steady"]


class StoryState:
    def __init__(self, world: World, hero: Entity, friend: Entity, villain: Entity, tool: Tool):
        self.world = world
        self.hero = hero
        self.friend = friend
        self.villain = villain
        self.tool = tool


def setup_world(params: StoryParams) -> StoryState:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero_name, hero_type, hero_label = HEROES[params.hero]
    friend_name, friend_type, friend_label = FRIENDS[params.friend]
    villain_name, villain_type, villain_label = VILLAINS[params.villain_variant]
    tool = TOOLS[params.tool]

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_label))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, label=friend_label))
    villain = world.add(Entity(id=villain_name, kind="character", type=villain_type, label=villain_label))
    world.add(Entity(id=tool.id, kind="thing", type=tool.kind, label=tool.label, phrase=tool.phrase))

    world.facts.update(hero=hero, friend=friend, villain=villain, tool=tool, setting=setting)
    return StoryState(world, hero, friend, villain, tool)


def tool_is_at_risk(tool: Tool) -> bool:
    return tool.id in {"plasticene", "ramen"}


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.hero not in HEROES:
        raise StoryError("Unknown hero.")
    if params.friend not in FRIENDS:
        raise StoryError("Unknown friend.")
    if params.villain_variant not in VILLAINS:
        raise StoryError("Unknown villain variant.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if not tool_is_at_risk(TOOLS[params.tool]):
        raise StoryError("The chosen object does not create a clear conflict.")
    if params.tool == "ramen" and params.place == "rooftop":
        return


def predict_bump(state: StoryState) -> dict[str, bool]:
    tool = state.tool
    if tool.id == "plasticene":
        return {"risk": True, "fix": True}
    if tool.id == "ramen":
        return {"risk": True, "fix": True}
    return {"risk": False, "fix": False}


def tell_story(state: StoryState, trait: str) -> None:
    w, hero, friend, villain, tool = state.world, state.hero, state.friend, state.villain, state.tool

    w.say(
        f"{hero.id} was a {trait} little hero who kept watch over {w.setting.place}."
    )
    w.say(
        f"{friend.id} was {hero.pronoun('possessive')} best friend, and {friend.id} loved {tool.phrase}."
    )
    w.say(
        f"Together they liked the calm part of the day, when {w.setting.backdrop} looked almost like a comic page."
    )

    w.para()
    w.say(
        f"One day, {friend.id} sat down with {tool.phrase} when {villain.id} swooped in with a mean grin."
    )
    if tool.id == "ramen":
        w.say(
            f"{villain.id} tried to grab the bowl of ramen and laughed, saying the lunch was too easy to spoil."
        )
    else:
        w.say(
            f"{villain.id} tried to crush the plasticene model and said tiny art did not matter."
        )
    hero.memes = {"worry": 1.0, "friendship": 1.0, "conflict": 1.0}
    friend.memes = {"hurt": 1.0}
    villain.memes = {"mean": 1.0}

    w.para()
    if tool.id == "plasticene":
        w.say(
            f"{hero.id} did not strike first. Instead, {hero.pronoun()} stepped between them and used {hero.pronoun('possessive')} hands to shield the plasticene."
        )
        w.say(
            f"{hero.id} said, \"You can mock me, but you do not get to smash my friend's work.\""
        )
        w.say(
            f"The villain_variant's grin faded, because the calm shield was stronger than a loud boast."
        )
    else:
        w.say(
            f"{hero.id} moved fast, caught the ramen bowl before it spilled, and set it safely on a bench."
        )
        w.say(
            f"Then {hero.id} turned to {villain.id} and said, \"If you want attention, use your own hands and leave our lunch alone.\""
        )
        w.say(
            f"The quick rescue left no mess, and the rude grin had nowhere to go."
        )

    hero.memes["pride"] = 1.0
    friend.memes["relief"] = 1.0
    friend.memes["trust"] = 1.0
    hero.memes["conflict"] = 0.0

    w.para()
    w.say(
        f"{friend.id} smiled at {hero.id}, because {hero.id} had protected both the {tool.label} and their friendship."
    )
    w.say(
        f"Together they stood in {w.setting.place} while {villain.id} backed away, and the day felt safe again."
    )

    w.facts.update(resolved=True, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    tool = f["tool"]
    return [
        f'Write a short superhero story with the words "variant", "plasticene", and "ramen".',
        f"Tell a child-friendly story where {hero.id} protects {friend.id}'s {tool.label} from a rude variant and saves the friendship.",
        f"Write a tiny superhero adventure in which a friend, a conflict, and {tool.label} lead to a brave, kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    villain = f["villain"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who protected {friend.id} and the {tool.label}?",
            answer=f"{hero.id} protected {friend.id} and kept {tool.phrase} safe.",
        ),
        QAItem(
            question=f"What did the variant try to do to the {tool.label}?",
            answer=(
                f"{villain.id} tried to ruin the {tool.label}. "
                f"That created the conflict in the story."
            ),
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {friend.id}?",
            answer=(
                f"They ended as closer friends. {hero.id} chose a careful hero move, "
                f"and {friend.id} felt safe and happy again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is plasticene?",
            answer="Plasticene is a soft, shapeable material that people can press and mold into little models.",
        ),
        QAItem(
            question="What is ramen?",
            answer="Ramen is a noodle soup with a warm broth, noodles, and often toppings like vegetables or egg.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and wanting them to feel safe and happy.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or struggle that the characters have to face before things can get better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H). friend(F). villain(V). tool(T).
risk(T) :- tool(T), (T = plasticene; T = ramen).
conflict(H,F,V,T) :- hero(H), friend(F), villain(V), tool(T), risk(T).
resolved(H,F,T) :- conflict(H,F,_,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend", fid))
    for vid in VILLAINS:
        lines.append(asp.fact("villain", vid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show conflict/4.\n#show resolved/3.")
    model = asp.one_model(program)
    conflicts = set(asp.atoms(model, "conflict"))
    resolved = set(asp.atoms(model, "resolved"))
    py_conflicts = set()
    py_resolved = set()
    for hid in HEROES:
        for fid in FRIENDS:
            for vid in VILLAINS:
                for tid in TOOLS:
                    if tool_is_at_risk(TOOLS[tid]):
                        py_conflicts.add((hid, fid, vid, tid))
                        py_resolved.add((hid, fid, tid))
    if conflicts and resolved and len(conflicts) == len(py_conflicts) and len(resolved) == len(py_resolved):
        print(f"OK: ASP parity matches Python ({len(conflicts)} conflicts).")
        return 0
    print("Mismatch between ASP and Python gates.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with friendship and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--villain-variant", choices=VILLAINS, dest="villain_variant")
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    friend = args.friend or rng.choice(list(FRIENDS))
    villain_variant = args.villain_variant or rng.choice(list(VILLAINS))
    tool = args.tool or rng.choice(list(TOOLS))
    params = StoryParams(place=place, hero=hero, friend=friend, villain_variant=villain_variant, tool=tool)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    state = setup_world(params)
    trait = random.Random(params.seed if params.seed is not None else 0).choice(TRAITS)
    tell_story(state, trait)
    return StorySample(
        params=params,
        story=state.world.render(),
        prompts=generation_prompts(state.world),
        story_qa=story_qa(state.world),
        world_qa=world_knowledge_qa(state.world),
        world=state.world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="city", hero="spark", friend="milo", villain_variant="variant", tool="plasticene"),
    StoryParams(place="park", hero="nova", friend="mina", villain_variant="mirror_variant", tool="ramen"),
    StoryParams(place="rooftop", hero="comet", friend="tess", villain_variant="variant", tool="plasticene"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show conflict/4."))
    return sorted(set(asp.atoms(model, "conflict")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict/4.\n#show resolved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show conflict/4.\n#show resolved/3."))
        print(f"conflicts: {len(asp.atoms(model, 'conflict'))}")
        print(f"resolved: {len(asp.atoms(model, 'resolved'))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, p in enumerate(CURATED):
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
