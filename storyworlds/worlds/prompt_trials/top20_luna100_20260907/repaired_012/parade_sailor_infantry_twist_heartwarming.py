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
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Parade:
    name: str
    setting: str
    route: str
    crowd_warmth: float = 0.0
    formation_ready: bool = False
    twist_revealed: bool = False
    heart_lift: float = 0.0
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    sailor_name: str
    infantry_name: str
    parade_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nora", "Sam", "Tavi", "June", "Ira", "Pia"]
PARADE_NAMES = ["The Lantern Parade", "The Harbor Parade", "The Morning Stars Parade", "The Welcome Parade"]


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
        "key": "borrowed_drum",
        "premise": [
            "On a bright morning, sailor {sailor} polished a little blue flag while infantry guide {infantry} lined up the children for {parade}. The harbor street smelled of bread and salt.",
            "Sailor {sailor} had practiced a cheerful wave for {parade}, and infantry guide {infantry} carried the parade map. Families gathered beneath strings of paper stars.",
        ],
        "problem": [
            "Just before the march began, the parade drum split with a soft pop. Without its beat, the sailors and infantry could not keep their steps together.",
            "The drummer's hands trembled, and the old drum made no sound. The waiting crowd grew quiet because the parade seemed ready to fall apart.",
        ],
        "conflict": [
            "\"We should cancel,\" said {sailor}. \"We should march quietly,\" replied {infantry}. Their two plans pulled the parade in different directions.",
            "{sailor} wanted to find another drum at once. {infantry} pointed to the waiting children. \"They are ready now,\" they said, and both felt worried.",
        ],
        "turn": [
            "Then a small girl near the front lifted two wooden spoons. She tapped them together and asked, \"Could my heartbeat be the parade beat?\"",
            "An old baker brought out an empty flour tin. {infantry} tapped its side, and {sailor} noticed that the children were already clapping in time.",
        ],
        "action": [
            "{sailor} smiled and raised the blue flag. {infantry} led the first row, while the children tapped spoons and clapped a gentle beat down the street.",
            "\"We do not need a perfect drum,\" {sailor} said. {infantry} nodded, and together they turned the flour tin, spoons, and claps into music.",
        ],
        "resolution": [
            "The parade moved forward with a sound made by everyone. The sailors and infantry stayed together, and the worried crowd began to smile.",
            "Soon every window joined the rhythm. The broken drum no longer mattered because the whole neighborhood had become the band.",
        ],
        "ending": [
            "At the harbor square, {sailor} hung the blue flag beside the little girl's spoons, and both shone in the afternoon sun.",
            "The flour tin rested at the front of the parade, covered with bright handprints from the children who had saved the music.",
        ],
        "problem_fact": "the parade drum split and could not keep the marchers together",
        "clue_fact": "children's spoons and claps revealed that the crowd could make a shared beat",
        "action_fact": "the sailors, infantry, and children made music together",
        "outcome_fact": "the parade continued with the whole neighborhood as its band",
    },
    {
        "key": "hidden_welcome",
        "premise": [
            "Sailor {sailor} and infantry guide {infantry} prepared {parade} along a quiet town road. They carried ribbons for a visiting ship and waved to every neighbor.",
            "The town planned a warm welcome parade, with sailor {sailor} at the front and infantry guide {infantry} beside the banner. Colorful flags fluttered above the road.",
        ],
        "problem": [
            "The guest ship never appeared at the meeting place. The parade waited so long that the flags drooped and the crowd began to wonder whether anyone was coming.",
            "A thick fog covered the harbor, hiding the arriving sailors. The welcome parade had no guest to greet, and its bright beginning felt suddenly lonely.",
        ],
        "conflict": [
            "\"We should go home,\" {sailor} said. \"We should keep the welcome ready,\" answered {infantry}. Neither knew how long hope could last.",
            "{sailor} wanted to send the band toward the harbor. {infantry} worried that the marching children would get lost in the fog. Their disagreement stopped the parade.",
        ],
        "turn": [
            "A child noticed tiny bell sounds beyond the fog. Then another child answered with a ribbon wave. The hidden guests were following the parade's sound.",
            "{infantry} listened carefully and heard a soft whistle from the water. {sailor} held up the brightest flag, and a matching light blinked back through the fog.",
        ],
        "action": [
            "They changed the plan. {sailor} led the parade slowly toward the harbor while {infantry} placed lanterns along the safe road for the unseen guests.",
            "\"Let us make a path instead of waiting at one spot,\" said {infantry}. {sailor} agreed, and the marchers carried bells and lanterns into the fog.",
        ],
        "resolution": [
            "The visiting sailors followed the bells and stepped into the lantern line. The welcome had worked because the parade had reached out first.",
            "When the fog lifted, the guests stood among them, smiling and waving. The parade became a welcome for everyone who had been waiting.",
        ],
        "ending": [
            "The last lantern glowed beside the harbor, where sailor {sailor} and infantry guide {infantry} shared a ribbon with their new friends.",
            "The flags rose again in the clear air, and the once-hidden ship answered with three happy blasts.",
        ],
        "problem_fact": "fog hid the visiting sailors from the waiting welcome parade",
        "clue_fact": "small bells and a blinking light showed that the guests were nearby",
        "action_fact": "they carried lanterns and bells along a safe path into the fog",
        "outcome_fact": "the hidden guests found the parade and joined the welcome",
    },
    {
        "key": "quiet_flag",
        "premise": [
            "Before {parade}, sailor {sailor} carefully folded a bright signal flag while infantry guide {infantry} checked the marching line. The town square was full of excited families.",
            "Sailor {sailor} was proud to carry the first flag in {parade}. Infantry guide {infantry} practiced the turns with the young marchers beneath a warm yellow sun.",
        ],
        "problem": [
            "A gust tore the flag from its pole and carried it over a tall wall. The parade could not see its turning signal, so everyone stopped at the corner.",
            "The flag's bright cloth vanished just before the parade's most important turn. The marchers stood still, afraid that one wrong step would scatter them.",
        ],
        "conflict": [
            "\"We can march without it,\" {sailor} said. \"The smallest marchers need a clear sign,\" {infantry} replied. Their concern made both voices tense.",
            "{sailor} wanted to climb the wall. {infantry} shook their head because the wall was slippery. The parade waited while the two friends searched for a safer answer.",
        ],
        "turn": [
            "A twist appeared when the youngest marcher opened a tiny paper fan. Its colors matched the lost flag, and she held it high from the corner.",
            "Then {infantry} saw that the parade's ribbons could be tied together. They would make a long, colorful signal that no wall could hide.",
        ],
        "action": [
            "{sailor} tied the ribbons into a bright streamer, and {infantry} carried it safely above the line. The young marcher waved her paper fan at every turn.",
            "\"Your little fan can lead us,\" said {sailor}. {infantry} smiled and used the linked ribbons to guide the parade around the corner.",
        ],
        "resolution": [
            "The marchers found their rhythm again and completed the route. The missing flag had led them to discover a signal made by many hands.",
            "The parade turned safely, and a neighbor returned the flag from the other side of the wall. Everyone cheered for the tiny fan that had solved the trouble.",
        ],
        "ending": [
            "At the square, the paper fan rested beside the recovered flag, small but bright enough to be remembered.",
            "The linked ribbons fluttered above the parade like one long rainbow made from many separate pieces.",
        ],
        "problem_fact": "a gust carried away the parade's turning flag",
        "clue_fact": "a child's colorful paper fan offered a new visible signal",
        "action_fact": "they linked parade ribbons and used the fan to guide the turns",
        "outcome_fact": "the marchers completed the route safely",
    },
    {
        "key": "empty_chair",
        "premise": [
            "Sailor {sailor} and infantry guide {infantry} arranged chairs beside {parade} for families and veterans. One small chair sat at the front beneath a yellow ribbon.",
            "The town prepared {parade} with banners, music, and a row of friendly chairs. Sailor {sailor} and infantry guide {infantry} saved the smallest chair for someone special.",
        ],
        "problem": [
            "The person meant for the yellow chair did not arrive. The parade was about to begin, but the empty seat made the front row feel sad.",
            "Everyone kept looking at the empty chair. {sailor} worried that the celebration would remind people of someone missing instead of making them happy.",
        ],
        "conflict": [
            "\"Move the chair away,\" said {sailor}. \"Leave it where it is,\" answered {infantry}. They both wanted kindness, but they imagined different kinds.",
            "{sailor} thought the parade should hide the empty seat. {infantry} believed it should remain an invitation. Their gentle disagreement made the opening wait.",
        ],
        "turn": [
            "A little boy placed a paper flower on the chair. He said, \"It can be for anyone who needs a place.\" The empty chair suddenly felt like an open door.",
            "An old neighbor explained that the missing guest had once welcomed lonely people. The twist was clear: the chair could continue that welcome.",
        ],
        "action": [
            "{sailor} placed a second flower on the chair, and {infantry} invited anyone nearby to sit there for one song at a time.",
            "\"Then it belongs to the next person who needs company,\" {sailor} said. {infantry} opened the parade with the yellow chair beside them.",
        ],
        "resolution": [
            "A shy newcomer sat down first, then a tired parent, then a laughing child. The chair became the warmest place in the parade.",
            "The crowd understood the invitation and made room for one another. The missing guest was remembered through the kindness that followed.",
        ],
        "ending": [
            "By sunset, the yellow chair held a pile of paper flowers and the soft glow of many grateful smiles.",
            "The little chair traveled at the front of the parade, no longer empty because it carried a welcome for everyone.",
        ],
        "problem_fact": "an empty yellow chair made the celebration feel lonely",
        "clue_fact": "a paper flower showed that the chair could welcome whoever needed company",
        "action_fact": "they left the chair open and invited people to share it",
        "outcome_fact": "the chair became a symbol of welcome during the parade",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.sailor_name, params.infantry_name, params.parade_name))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    parade = Parade(
        name=params.parade_name,
        setting="the town harbor road",
        route="harbor road to the town square",
    )
    world = World(parade)
    sailor = world.add(Entity(
        id=params.sailor_name,
        kind="character",
        type="sailor",
        label="sailor",
        phrase=f"sailor {params.sailor_name}",
    ))
    infantry = world.add(Entity(
        id=params.infantry_name,
        kind="character",
        type="infantry",
        label="infantry guide",
        phrase=f"infantry guide {params.infantry_name}",
    ))
    flag = world.add(Entity(
        id="welcome_flag",
        type="parade_flag",
        label="parade flag",
        phrase="a bright parade flag",
    ))

    rng = _rng_for(params)
    index = (params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)
    arc = ARCS[index]
    beats = ("premise", "problem", "conflict", "turn", "action", "resolution", "ending")
    if params.seed is None:
        chosen = {beat: rng.choice(arc[beat]) for beat in beats}
    else:
        code = (params.seed // len(ARCS)) % 128
        chosen = {beat: arc[beat][(code >> bit) % len(arc[beat])] for bit, beat in enumerate(beats)}

    values = {
        "sailor": sailor.id,
        "infantry": infantry.id,
        "parade": parade.name,
    }
    rendered = {beat: chosen[beat].format(**values) for beat in beats}
    for i, beat in enumerate(beats):
        if i:
            world.para()
        world.say(rendered[beat])

    parade.crowd_warmth = 1.0
    parade.formation_ready = True
    parade.twist_revealed = True
    parade.heart_lift = 1.0
    sailor.meters.update(energy=3.0, courage=4.0)
    infantry.meters.update(energy=3.0, patience=4.0)
    sailor.memes["hope"] = 1.0
    infantry.memes["hope"] = 1.0
    flag.meters["shared"] = 1.0

    parade.facts = {
        "sailor": sailor,
        "infantry": infantry,
        "flag": flag,
        "arc": arc,
        "rendered": rendered,
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.parade.facts
    return [
        "Write a heartwarming parade story about a sailor and an infantry guide who face an unexpected twist.",
        f"Tell a child-friendly story in which {f['sailor'].id} and {f['infantry'].id} solve a parade problem by listening to someone unexpected.",
        "Create a warm parade tale whose ending shows that many small acts can make a celebration brighter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.parade.facts
    return [
        QAItem(
            question=f"Who led {world.parade.name}?",
            answer=f"{f['sailor'].id}, a sailor, and {f['infantry'].id}, an infantry guide, helped lead {world.parade.name}.",
        ),
        QAItem(
            question="What problem interrupted the parade?",
            answer=f["rendered"]["problem"],
        ),
        QAItem(
            question="What twist changed the plan?",
            answer=f["rendered"]["turn"],
        ),
        QAItem(
            question="How was the parade saved?",
            answer=f"{f['rendered']['action']} {f['rendered']['resolution']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized line or procession of people, music, flags, or decorated vehicles moving together for others to watch.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or travels in a boat or ship and helps care for people, equipment, and the journey.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who travel and work on foot. In this story, the infantry guide helps people move safely and kindly together.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change or discovery that sends the story in a new direction.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {entity.id:12} ({entity.type:12}) {' '.join(parts)}")
    lines.extend(
        [
            f"  parade.name={world.parade.name}",
            f"  parade.route={world.parade.route}",
            f"  parade.crowd_warmth={world.parade.crowd_warmth}",
            f"  parade.formation_ready={world.parade.formation_ready}",
            f"  parade.twist_revealed={world.parade.twist_revealed}",
            f"  parade.heart_lift={world.parade.heart_lift}",
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :-
    has_theme(parade),
    has_role(sailor),
    has_role(infantry),
    has_feature(twist),
    has_style(heartwarming).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("has_theme", "parade"),
            asp.fact("has_role", "sailor"),
            asp.fact("has_role", "infantry"),
            asp.fact("has_feature", "twist"),
            asp.fact("has_style", "heartwarming"),
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
    asp_ok = any(sym.name == "valid_story" for sym in model)
    sample = generate(StoryParams("Luna", "Milo", "The Lantern Parade", seed=12))
    prose = sample.story.lower()
    prose_ok = all(word in prose for word in ("parade", "sailor", "infantry"))
    if asp_ok and prose_ok and sample.world is not None and sample.world.parade.twist_revealed:
        print("OK: ASP and Python recognize the parade, sailor, infantry, and twist story.")
        return 0
    print("MISMATCH: ASP and Python story checks disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming parade world with a sailor, infantry guide, and a twist."
    )
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
    infantry_choices = [name for name in NAMES if name != sailor]
    infantry = args.infantry_name or rng.choice(infantry_choices)
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
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
            model = asp.one_model(asp_program())
            if any(sym.name == "valid_story" for sym in model):
                print("1 compatible heartwarming parade pattern: parade + sailor + infantry + twist")
            else:
                print("No compatible story pattern found.")
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Milo", "The Lantern Parade", seed=0),
            StoryParams("Nora", "Sam", "The Harbor Parade", seed=1),
            StoryParams("Tavi", "June", "The Welcome Parade", seed=2),
            StoryParams("Ira", "Pia", "The Morning Stars Parade", seed=3),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(args.n * 50, 50)
        while len(samples) < args.n and index < limit:
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
