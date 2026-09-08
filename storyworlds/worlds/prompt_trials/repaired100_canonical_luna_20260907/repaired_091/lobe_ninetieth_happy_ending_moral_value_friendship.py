#!/usr/bin/env python3
"""
A gentle whodunit about a missing lobe-shaped keepsake, a ninetieth birthday,
friendship, and the happy ending that comes from telling the truth.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    hall: str = "Willow Hall"
    hero: str = "Luna"
    friend: str = "Milo"
    guest: str = "Grandma June"
    keepsake: str = "the silver lobe-shaped pin"
    seed: Optional[int] = None


CASES = (
    {
        "name": "the ribbon box",
        "object": "the silver lobe-shaped pin",
        "clue": "a tiny silver thread beside the ribbon box",
        "first_guess": "They first wondered whether a careless guest had carried it home.",
        "cause": "the pin had slipped through a loose fold in the box lining and rested beneath the display cloth",
        "repair": "Luna and Milo lifted the cloth with Grandma June's permission and found the pin without disturbing the cake or gifts",
        "dialogue": '"Look at the thread, not at the guests," Milo said. "Then we can search kindly," Luna replied.',
        "change": "Grandma June's worry softened into a laugh when the keepsake was found",
        "ending": "the silver lobe-shaped pin shone beside the ninetieth candle while everyone clapped",
        "lesson": "friends solve problems best when they follow evidence instead of blaming people",
    },
    {
        "name": "the blue vase",
        "object": "the blue lobe-shaped vase",
        "clue": "a damp crescent on the table leading toward the flower cart",
        "first_guess": "They suspected that a mischievous child had moved it as a prank.",
        "cause": "the vase had been carried to the flower cart so a spilled drink could be wiped from the birthday table",
        "repair": "the florist showed them the clean cart and returned the vase to its marked place",
        "dialogue": '"The crescent points to wheels," Luna said. "So let us ask the florist before we accuse anyone," Milo answered.',
        "change": "the nervous guests became relieved helpers and made a clearer place for the vase",
        "ending": "the blue lobe-shaped vase held daisies beside Grandma June's ninetieth birthday cake",
        "lesson": "friendship grows when people ask questions before making accusations",
    },
    {
        "name": "the vanished invitation",
        "object": "the cream invitation with a lobe-shaped seal",
        "clue": "a matching scrap of cream paper under the piano bench",
        "first_guess": "They thought someone had hidden the special invitation to spoil the party.",
        "cause": "the invitation had slid under the bench when a gust from the open door lifted the tablecloth",
        "repair": "Luna closed the door gently, Milo checked beneath the bench, and they placed the invitation in a safe frame",
        "dialogue": '"The paper traveled with the wind," Milo said. "Then the door is our next clue," Luna replied.',
        "change": "the empty place at the table became a welcoming seat for the late-arriving guest",
        "ending": "the cream seal rested on the frame as the ninetieth birthday song began",
        "lesson": "careful friends turn a frightening mystery into a chance to welcome someone",
    },
    {
        "name": "the quiet music box",
        "object": "the little music box with a lobe-shaped lid",
        "clue": "a line of glitter running from the music box to the gift table",
        "first_guess": "They wondered if the box had been opened by a secret visitor.",
        "cause": "the music box had been moved so glitter from its decoration would not fall into the soup",
        "repair": "the cook pointed out the safe shelf, and Luna wound the box only after asking permission",
        "dialogue": '"A safe place can explain a quiet box," Luna said. "Let us check the table before the story grows," Milo agreed.',
        "change": "Grandma June stopped worrying about the missing tune and invited everyone to dance",
        "ending": "the lobe-shaped lid opened, and a bright tune joined the ninetieth birthday applause",
        "lesson": "good friends protect both people and objects while they search for the truth",
    },
    {
        "name": "the backwards banner",
        "object": "the gold lobe-shaped birthday banner",
        "clue": "fresh tape on the back of the banner and letters visible through its fold",
        "first_guess": "They believed someone had torn away the words honoring Grandma June.",
        "cause": "the banner had folded backward when a helper tried to keep it dry near the window",
        "repair": "the helper unfolded it with Luna and Milo and taped its corners away from the draft",
        "dialogue": '"The letters are still here," Milo said. "A fold is not a disappearance," Luna answered.',
        "change": "the helper who had felt ashamed proudly helped hang the banner again",
        "ending": "the gold lobe-shaped banner welcomed everyone to the ninetieth birthday",
        "lesson": "kind friendship gives people room to admit mistakes and make them right",
    },
)

OPENINGS = (
    "On the morning of a very special birthday, a small mystery appeared at Willow Hall.",
    "Willow Hall smelled of cinnamon and flowers when Luna noticed that something was missing.",
    "The party for Grandma June's ninetieth birthday was nearly ready when the whodunit began.",
    "Balloons bobbed above Willow Hall, but one important keepsake had vanished.",
    "Luna and Milo had promised to help with the birthday table, so they noticed the empty space at once.",
)

BRIDGES = (
    "They made a quiet list of what they knew, what they had guessed, and what still needed checking.",
    "Instead of searching through people's bags, they studied the room and asked the adults for permission.",
    "The friends compared the timing, the nearby objects, and the marks on the table.",
    "They agreed that a clue should point toward an explanation, not toward a person to blame.",
    "Milo watched the floor while Luna watched the tables, and both friends reported exactly what they saw.",
)

@dataclass
class World:
    hall: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(params: StoryParams) -> World:
    if not params.hero.strip() or not params.friend.strip() or not params.guest.strip():
        raise StoryError("hero, friend, and guest names must not be empty")
    if params.hero.strip().lower() == params.friend.strip().lower():
        raise StoryError("hero and friend must have different names")
    if params.seed is not None and not isinstance(params.seed, int):
        raise StoryError("seed must be an integer")

    rng = random.Random(params.seed if params.seed is not None else 0)
    case = CASES[rng.randrange(len(CASES))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))]
    bridge = BRIDGES[rng.randrange(len(BRIDGES))]
    object_name = case["object"]
    hero = params.hero
    friend = params.friend
    guest = params.guest

    world = World(params.hall)
    world.add(Entity(hero, "character", "girl", hero, traits=["curious", "kind"]))
    world.add(Entity(friend, "character", "boy", friend, traits=["careful", "loyal"]))
    world.add(Entity(guest, "character", "woman", guest, traits=["generous", "nervous"]))
    world.add(Entity("keepsake", "object", "keepsake", object_name, owner=guest))

    for entity in world.entities.values():
        if entity.kind == "character":
            entity.memes.update(friendship=1, trust=1)
    world.entities[guest].memes["worry"] = 1
    world.entities["keepsake"].meters.update(visible=0, safe=1)

    world.facts = {
        "case": case["name"],
        "object": object_name,
        "clue": case["clue"],
        "first_guess": case["first_guess"],
        "cause": case["cause"],
        "repair": case["repair"],
        "dialogue": case["dialogue"],
        "change": case["change"],
        "ending": case["ending"],
        "lesson": case["lesson"],
        "hero": hero,
        "friend": friend,
        "guest": guest,
        "opening": opening,
        "bridge": bridge,
        "ninetieth": "ninetieth",
        "lobe": "lobe",
    }

    world.say(opening)
    world.say(
        f"{hero} and {friend} were helping prepare {guest}'s ninetieth birthday. "
        f"The guests would arrive soon, and the keepsake belonged safely to {guest}."
    )
    world.say(f"Then they discovered the mystery of {case['name']}: {object_name} was gone from its place.")
    world.para()
    world.say(case["first_guess"])
    world.say(bridge)
    world.say(f"{hero} found the useful clue: {case['clue']}.")
    world.say(case["dialogue"])
    world.say(f"They asked the grown-ups before touching anything. {case['repair']}.")
    world.entities["keepsake"].meters["visible"] = 1
    world.entities["keepsake"].memes["returned"] = 1
    world.entities[guest].memes["worry"] = 0
    world.para()
    world.say(f"The clue revealed the cause: {case['cause']}.")
    world.say(f"The mystery ended happily because {case['repair']}.")
    world.say(f"{case['change']}.")
    world.say(
        f'"We solved it without blaming anyone," {friend} told {hero}. '
        f'"That is what friends do," {hero} replied.'
    )
    world.entities[hero].memes["friendship"] = 2
    world.entities[friend].memes["friendship"] = 2
    world.para()
    world.say(f"They remembered the moral value that {case['lesson']}.")
    world.say(f"At last, {case['ending']}.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly whodunit at {world.hall} about {f['object']} missing before a ninetieth birthday.",
        f"Use the clue '{f['clue']}' to reveal that {f['cause']}.",
        f"Include friendship, a happy ending, and the moral value that {f['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What was missing during {f['guest']}'s ninetieth birthday preparation?",
            answer=f"{f['object']} was missing from its place at {world.hall}.",
        ),
        QAItem(
            question="What clue helped the friends solve the whodunit?",
            answer=f"They noticed that {f['clue']}.",
        ),
        QAItem(
            question="What had really happened?",
            answer=f"They learned that {f['cause']}.",
        ),
        QAItem(
            question="How did the friends handle the mystery?",
            answer=f"They asked permission, followed physical evidence, and avoided blaming anyone. {f['repair']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The keepsake was safe again, {f['guest']} felt happy, and {f['ending']}.",
        ),
        QAItem(
            question="What moral value did the friends show?",
            answer=f"They showed that {f['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ninetieth mean?",
            answer="Ninetieth means number ninety in an order, such as a ninetieth birthday.",
        ),
        QAItem(
            question="What is a lobe?",
            answer="A lobe is a rounded part of something, such as a rounded section of an ear or an object shaped like one.",
        ),
        QAItem(
            question="Why is friendship useful during a mystery?",
            answer="Friendship helps people listen, compare clues, stay calm, and solve a problem without unfairly blaming others.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


ASP_RULES = r"""
character(X) :- person(X).
keepsake_safe(K) :- keepsake(K), found(K), handled_carefully(K).
solved(C) :- clue(C), cause_known(C), keepsake_safe(K).
friendship(H,F) :- person(H), person(F), trust(H), trust(F), solved(clue).
happy_ending(G) :- guest(G), keepsake_safe(K), celebration_ready.
moral_value :- evidence_first, no_blame.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    facts = [
        asp.fact("person", "luna"),
        asp.fact("person", "milo"),
        asp.fact("guest", "june"),
        asp.fact("keepsake", "silver_lobe_pin"),
        asp.fact("found", "silver_lobe_pin"),
        asp.fact("handled_carefully", "silver_lobe_pin"),
        asp.fact("clue", "thread"),
        asp.fact("cause_known", "thread"),
        asp.fact("trust", "luna"),
        asp.fact("trust", "milo"),
        asp.fact("celebration_ready"),
        asp.fact("evidence_first"),
        asp.fact("no_blame"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program(
        "#show keepsake_safe/1.\n"
        "#show solved/1.\n"
        "#show friendship/2.\n"
        "#show happy_ending/1.\n"
        "#show moral_value/0.\n"
    )
    model = asp.one_model(program)
    names = {(symbol.name, len(symbol.arguments)) for symbol in model}
    needed = {
        ("keepsake_safe", 1),
        ("solved", 1),
        ("friendship", 2),
        ("happy_ending", 1),
        ("moral_value", 0),
    }
    if not names >= needed:
        print("MISMATCH: ASP rules did not produce the expected story facts.")
        return 1
    sample = generate(StoryParams(seed=17))
    if "ninetieth" not in sample.story or "friend" not in sample.story.lower():
        print("MISMATCH: generated story failed narrative checks.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A friendly birthday whodunit about a lobe-shaped keepsake."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--hall", default="Willow Hall")
    parser.add_argument("--hero", default=None)
    parser.add_argument("--friend", default=None)
    parser.add_argument("--guest", default=None)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Nora", "Iris", "Maya"])
    friend = args.friend or rng.choice(["Milo", "Theo", "Sam", "Owen"])
    guest = args.guest or rng.choice(["Grandma June", "Aunt Rosa", "Grandpa Eli", "Mrs. Pearl"])
    if hero.lower() == friend.lower():
        raise StoryError("hero and friend must have different names")
    return StoryParams(
        hall=args.hall,
        hero=hero,
        friend=friend,
        guest=guest,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(
            asp_program(
                "#show keepsake_safe/1.\n"
                "#show solved/1.\n"
                "#show friendship/2.\n"
                "#show happy_ending/1.\n"
                "#show moral_value/0.\n"
            )
        )
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(
            asp_program(
                "#show keepsake_safe/1.\n"
                "#show solved/1.\n"
                "#show friendship/2.\n"
                "#show happy_ending/1.\n"
                "#show moral_value/0.\n"
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        case_count = len(CASES)
        for index in range(case_count):
            params = StoryParams(
                hall=args.hall,
                hero=args.hero or "Luna",
                friend=args.friend or "Milo",
                guest=args.guest or "Grandma June",
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + attempt))
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
