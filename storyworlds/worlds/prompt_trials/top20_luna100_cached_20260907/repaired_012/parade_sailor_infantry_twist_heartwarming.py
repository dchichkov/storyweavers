#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Parade:
    name: str
    route: str
    crowd_joy: float = 0.0
    rhythm: float = 0.0
    delay: float = 0.0
    heart_open: bool = False
    twist_revealed: bool = False
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    sailor_name: str
    infantry_name: str
    parade_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nora", "Theo", "Iris", "Sam", "Pia", "Owen"]
PARADE_NAMES = ["The Lantern Parade", "The Harbor Parade", "The Spring Welcome", "The Golden Drum Parade"]
ROUTES = ["the old harbor road", "the town square", "the hill by the lighthouse", "the sunny market street"]


class World:
    def __init__(self, parade: Parade) -> None:
        self.parade = parade
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

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


ARCS = [
    {
        "key": "quiet_drum",
        "premise": [
            "{sailor} polished a little brass whistle before {parade} began along {route}. Beside the flags marched {infantry}, a kind infantry drummer who kept one hand close to a small red drum.",
            "The town prepared for {parade}, and {sailor} helped guide the banners while {infantry} carried the parade drum. Everyone expected a bright, noisy walk along {route}.",
        ],
        "problem": [
            "But the drum made no sound. Without its beat, the parade slowed, the flags drooped, and the waiting children began to wonder whether the celebration would start.",
            "At the first corner, the drum gave only a tiny puff. The marching rhythm disappeared, and the parade stopped beside a bakery while the crowd grew quiet.",
        ],
        "conflict": [
            "\"We should march without music,\" said {sailor}. \"We should fix the drum first,\" replied {infantry}. Their two plans pulled the parade in different directions.",
            "{sailor} wanted to borrow a louder bell, but {infantry} shook their head. \"This drum has a voice,\" they said. \"We just have not heard it yet.\"",
        ],
        "turn": [
            "Then a small child in the crowd tugged {sailor}'s sleeve and whispered, \"The drum is not broken. It is waiting for someone.\" {infantry} knelt beside the child and noticed a loose ribbon tied inside the drum.",
            "An old woman near the curb offered a warm smile and said, \"Listen below the quiet.\" {sailor} held the drum still while {infantry} found a paper star tucked beneath its skin.",
        ],
        "action": [
            "{sailor} untied the ribbon while {infantry} tapped the drum softly. The paper star showed a simple rhythm, and soon the sailor's whistle joined the gentle beat.",
            "\"Try the little beat first,\" said {sailor}. {infantry} nodded, tapped twice, paused, and tapped once more. The drum answered as if it had been waiting for that exact welcome.",
        ],
        "resolution": [
            "The parade moved again, not with a grand roar but with a warm, steady rhythm. Children clapped, and {sailor} and {infantry} smiled because the quiet drum had brought everyone closer.",
            "The crowd began to clap along. {infantry} led with the small drum, while {sailor} guided the flags, and the parade reached the square with every face shining.",
        ],
        "ending": [
            "At sunset, the paper star rested on the drum, and the smallest children were allowed to tap its happy beat.",
            "The red drum glowed beside the harbor lanterns, still carrying the gentle rhythm that had made strangers feel like friends.",
        ],
        "problem_fact": "the parade drum fell silent and stopped the march",
        "clue_fact": "a child and a hidden paper star revealed that the drum needed a gentle rhythm",
        "action_fact": "the sailor and infantry drummer followed the small rhythm together",
        "outcome_fact": "the parade resumed and the crowd joined as one",
    },
    {
        "key": "backward_banner",
        "premise": [
            "{sailor} carried the town banner at the front of {parade}, while {infantry} marched beside the musicians along {route}. The morning air smelled of fresh bread and rain.",
            "Flags fluttered above {parade} as {sailor} checked the ropes and {infantry} helped the younger marchers keep step. The whole town was ready to welcome its visitors.",
        ],
        "problem": [
            "A sudden gust turned the main banner backward. It pointed the parade away from the square, and every turn made the marchers circle the same fountain.",
            "The banner's arrow seemed to choose the wrong road. Soon the parade had returned to its starting place, and the tired crowd feared the welcome would be missed.",
        ],
        "conflict": [
            "\"Trust the banner,\" said {sailor}. \"Trust the people who know the town,\" answered {infantry}. They disagreed while the marching feet shuffled in place.",
            "{sailor} wanted to pull the flag straight. {infantry} wanted to ask the quietest people what they saw. Neither plan began because both were waiting for the other.",
        ],
        "turn": [
            "A little girl pointed to the banner's back and found a stitched picture of a blue door. {infantry} recognized it as the door of the town's lonely lighthouse keeper.",
            "An old sailor in the crowd turned the flag around and laughed softly. The hidden side showed a blue door, the sign of a person who had never been able to attend a parade.",
        ],
        "action": [
            "{sailor} lowered the banner, and {infantry} led the parade toward the blue door. They changed the route not because the flag was wrong, but because it was asking them to notice someone.",
            "\"Let us make the welcome smaller and kinder,\" said {sailor}. {infantry} nodded, and the marchers carried their music up the lighthouse path.",
        ],
        "resolution": [
            "The lighthouse keeper opened the door with tears in their eyes. The parade had not lost its way; it had found the person who needed it most.",
            "The keeper joined the final row, carrying a lantern. The crowd returned to the square feeling that the best celebration was one that made room for everyone.",
        ],
        "ending": [
            "The banner finally turned forward, and its blue door shone above the parade like a promise.",
            "At the square, the lighthouse keeper's lantern hung beside the banner, glowing warmly in the evening air.",
        ],
        "problem_fact": "a backward-turning banner led the parade in circles",
        "clue_fact": "the hidden banner showed a blue door belonging to a lonely lighthouse keeper",
        "action_fact": "the sailor and infantry guided the parade to the lighthouse",
        "outcome_fact": "the keeper joined the celebration and the route became meaningful",
    },
    {
        "key": "empty_chair",
        "premise": [
            "Before {parade} began, {sailor} placed a bright ribbon on an empty chair near {route}. {infantry} carried a small bouquet and wondered why the chair had been saved.",
            "{sailor} and {infantry} prepared {parade} beneath rows of paper suns. One chair stood at the front, with a folded scarf resting across it.",
        ],
        "problem": [
            "The guest of honor did not arrive. The music started, but the empty chair made the celebration feel unfinished, and the crowd grew worried.",
            "Everyone kept looking down the road for the missing guest. The parade could not decide whether to begin, because the empty chair seemed to hold the whole town's hope.",
        ],
        "conflict": [
            "\"We should start on time,\" said {sailor}. \"We should wait a little longer,\" said {infantry}. Their disagreement made the drumbeat stop before it began.",
            "{sailor} thought the chair should be moved. {infantry} said it should remain where the guest could see it. Both cared deeply, but they could not agree.",
        ],
        "turn": [
            "A note fell from the folded scarf. It explained that the missing guest was too shy to enter a crowd, and asked whether the parade could pass slowly by their window.",
            "The scarf held a simple message: the guest had helped build the parade but was afraid of being thanked. {sailor} understood that the empty chair was not waiting for applause, only kindness.",
        ],
        "action": [
            "{sailor} lifted the ribbon, and {infantry} carried the bouquet. Together they turned {parade} toward the small yellow house at the end of {route}.",
            "\"We can bring the parade to them,\" said {sailor}. {infantry} smiled and led the marchers in a quiet loop toward the shy builder's window.",
        ],
        "resolution": [
            "The guest peeked out, then stepped into the sunlight. The crowd clapped softly, and the empty chair became a place for them to rest beside their new friends.",
            "When the guest opened the window, the musicians played the gentlest song. The parade resumed with its honored helper walking beside the chair.",
        ],
        "ending": [
            "By evening, the bright ribbon had moved from the empty chair to the guest's coat.",
            "The chair stayed near the square, but now it held a basket of flowers and no longer looked lonely.",
        ],
        "problem_fact": "the guest of honor was missing and left an empty chair",
        "clue_fact": "a note revealed that the guest was shy and wanted the parade brought to their window",
        "action_fact": "the sailor and infantry led the parade to the guest",
        "outcome_fact": "the shy helper joined the celebration",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    key = "|".join((params.sailor_name, params.infantry_name, params.parade_name))
    seed = int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def tell(params: StoryParams) -> World:
    rng = _rng_for(params)
    index = (params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)
    arc = ARCS[index]
    parade = Parade(name=params.parade_name, route=rng.choice(ROUTES))
    world = World(parade)

    sailor = world.add(Entity(params.sailor_name, "character", "sailor", "sailor"))
    infantry = world.add(Entity(params.infantry_name, "character", "infantry", "infantry"))
    banner = world.add(Entity("banner", "thing", "flag", "parade banner"))
    drum = world.add(Entity("drum", "thing", "instrument", "small parade drum"))

    sailor.meters["energy"] = 4.0
    infantry.meters["energy"] = 4.0
    sailor.memes["care"] = 1.0
    infantry.memes["care"] = 1.0
    banner.meters["direction"] = 0.0
    drum.meters["voice"] = 0.0
    parade.crowd_joy = 0.2
    parade.delay = 1.0

    beats = ("premise", "problem", "conflict", "turn", "action", "resolution", "ending")
    chosen = {}
    for beat in beats:
        choices = arc[beat]
        chosen[beat] = choices[((params.seed or 0) // max(1, len(ARCS)) + len(beat)) % len(choices)] if params.seed is not None else rng.choice(choices)

    rendered = {}
    for beat in beats:
        text = chosen[beat].format(
            sailor=params.sailor_name,
            infantry=params.infantry_name,
            parade=params.parade_name,
            route=parade.route,
        )
        rendered[beat] = text
        if beat != "premise":
            world.para()
        world.say(text)

    parade.rhythm = 1.0
    parade.delay = 0.0
    parade.crowd_joy = 1.0
    parade.heart_open = True
    parade.twist_revealed = True
    sailor.meters["energy"] = 3.0
    infantry.meters["energy"] = 3.0
    drum.meters["voice"] = 1.0
    banner.meters["direction"] = 1.0

    parade.facts = {
        "sailor": sailor,
        "infantry": infantry,
        "banner": banner,
        "drum": drum,
        "arc": arc["key"],
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
        "problem_event": rendered["problem"],
        "turn_event": rendered["turn"],
        "action_event": rendered["action"],
        "resolution_event": rendered["resolution"],
    }
    return world


def generate_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming parade story with a sailor, an infantry helper, and a surprising twist.",
        f"Tell a child-friendly story about {world.parade.name} that stops, then discovers who truly needs the celebration.",
        "Write a gentle story where listening changes a parade's path and brings people together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.parade.facts
    sailor = f["sailor"].id
    infantry = f["infantry"].id
    return [
        QAItem(
            question=f"Who helped with {world.parade.name}?",
            answer=f"{sailor}, a sailor, and {infantry}, an infantry helper, worked together during the parade.",
        ),
        QAItem(
            question=f"What problem interrupted {world.parade.name}?",
            answer=f["problem_event"],
        ),
        QAItem(
            question="What surprising clue changed their plan?",
            answer=f["turn_event"],
        ),
        QAItem(
            question="How did the parade end?",
            answer=f"{f['action_event']} {f['resolution_event']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized celebration in which people walk, play music, carry signs or flags, and share a happy moment with a community.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works or travels on a boat or ship and knows how to move safely on the water.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry means soldiers who travel and work on foot. In this gentle story, the infantry helper is a caring person who marches with the group.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters understand, often revealing a new reason for the problem.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.type:10}) {' '.join(bits)}")
    lines.extend(
        [
            f"  parade.rhythm={world.parade.rhythm}",
            f"  parade.delay={world.parade.delay}",
            f"  parade.crowd_joy={world.parade.crowd_joy}",
            f"  parade.heart_open={world.parade.heart_open}",
            f"  parade.twist_revealed={world.parade.twist_revealed}",
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :-
    theme(parade),
    role(sailor),
    role(infantry),
    feature(twist),
    style(heartwarming),
    resolved.
resolved.
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("theme", "parade"),
            asp.fact("role", "sailor"),
            asp.fact("role", "infantry"),
            asp.fact("feature", "twist"),
            asp.fact("style", "heartwarming"),
            asp.fact("resolved"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if not any(symbol.name == "valid_story" for symbol in model):
        print("MISMATCH: ASP twin rejected the parade story.")
        return 1
    sample = generate(StoryParams("Luna", "Milo", "The Lantern Parade", seed=7))
    required = ("parade", "sailor", "infantry")
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story omitted a required narrative word.")
        return 1
    if not sample.world.parade.twist_revealed or not sample.world.parade.heart_open:
        print("MISMATCH: generated world did not resolve its twist.")
        return 1
    print("OK: Python and ASP agree on the heartwarming parade world.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming parade world with a sailor, infantry helper, and twist.")
    parser.add_argument("--sailor-name")
    parser.add_argument("--infantry-name")
    parser.add_argument("--parade-name", choices=PARADE_NAMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    sailor = args.sailor_name or rng.choice(NAMES)
    available = [name for name in NAMES if name != sailor]
    infantry = args.infantry_name or rng.choice(available)
    parade = args.parade_name or rng.choice(PARADE_NAMES)
    return StoryParams(sailor_name=sailor, infantry_name=infantry, parade_name=parade)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
            model = asp.one_model(asp_program())
            print("1 compatible heartwarming parade pattern" if model else "0 compatible patterns")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams("Luna", "Milo", "The Lantern Parade", seed=11),
            StoryParams("Nora", "Theo", "The Harbor Parade", seed=23),
            StoryParams("Iris", "Sam", "The Spring Welcome", seed=37),
        ]
        samples = [generate(params) for params in params_list]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n) and index < max(args.n * 50, 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
