#!/usr/bin/env python3
from __future__ import annotations

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
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))),
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class SceneState:
    setting: str = "the town square"
    parade_ready: bool = False
    twist_revealed: bool = False
    heart_full: bool = False
    crowd_smile: float = 0.0
    band_playing: bool = False
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    sailor_name: str
    infantry_name: str
    parade_name: str
    seed: Optional[int] = None


NAMES = ["Mina", "Toby", "Lena", "Arlo", "June", "Nico", "Pia", "Owen"]
PARADE_NAMES = ["Lantern Parade", "Harbor Parade", "Spring Parade", "Ribbon Parade"]


class World:
    def __init__(self, state: SceneState) -> None:
        self.state = state
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(_copy.deepcopy(self.state))
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        return w


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    stable = "|".join((params.sailor_name, params.infantry_name, params.parade_name))
    seed = int.from_bytes(hashlib.sha256(stable.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


ARCS = [
    {
        "premise": [
            "On the morning of the {parade}, sailor {sailor} arrived in the square with a brass whistle and a neat blue coat. Infantry captain {infantry} was arranging boots, banners, and a little wagon of cocoa for the march.",
            "The {parade} began by the harbor fountain, where sailor {sailor} helped set lanterns in a row while infantry leader {infantry} checked the drums and smiled at every child.",
        ],
        "problem": [
            "Then a strong gust turned the parade ribbons inside out and made the sailors' flags tangle with the infantry banners. The whole line slowed to a confused stop.",
            "A tiny twist in the route sent the parade past the bakery twice. The marching band stayed cheerful, but the children saw that the sailor and infantry line had begun to loop.",
        ],
        "conflict": [
            "\"March faster!\" said {sailor}. \"March steadier!\" said {infantry}. Their voices tangled with the ribbons, and the crowd grew quiet with worry.",
            "{sailor} wanted to pull the banner straight. {infantry} wanted to pause and re-tie it properly. For a moment, both plans seemed kind, but neither could start the parade moving.",
        ],
        "turn": [
            "A small child offered a warm cup of cocoa to both of them. They shared it, and their shoulders relaxed. Then they noticed the twist was not in the route at all, but in the banner rope.",
            "{infantry} and {sailor} took one quiet sip of cocoa together. The warmth made them look again, and they saw a tiny knot holding the parade in place like a ribbon bow.",
        ],
        "action": [
            "\"You hold the pole,\" said {infantry}. \"I will loosen the knot,\" said {sailor}. They worked side by side, careful and gentle, until the banner rope slipped free.",
            "{sailor} laughed softly. \"Good eye.\" {infantry} answered, \"Good hands.\" Together they untwisted the ribbon, then stepped back so the parade line could breathe again.",
        ],
        "resolution": [
            "The drums began again, the flags lifted straight, and the parade moved forward in one bright line. The crowd clapped because the twist had been solved with patience instead of hurry.",
            "With the knot gone, the sailor and infantry marched together at an easy pace. Their faces brightened, and the children cheered as the parade found its true path.",
        ],
        "ending": [
            "At the end of the street, lanterns glowed over smiling faces, and the little cocoa cups warmed the hands of everyone who had helped.",
            "The parade closed with soft music, straight banners, and a sky full of paper confetti drifting like tiny stars.",
        ],
        "problem_fact": "the parade route got twisted by a tangled banner rope",
        "clue_fact": "sharing cocoa helped them notice the twist was in the rope",
        "action_fact": "they loosened the knot together and straightened the banner",
        "outcome_fact": "the parade moved on in a bright, calm line",
    },
    {
        "premise": [
            "At the {parade}, sailor {sailor} carried a tray of lemon cakes for the marching band, while infantry friend {infantry} kept the lanterns lit along the sidewalk.",
            "Sailor {sailor} and infantry helper {infantry} joined the {parade} to welcome the harbor mayor home. Their feet kept time with the drums, and their hearts felt light.",
        ],
        "problem": [
            "A painted float rolled too close to the fountain and turned the parade path into a narrow curve. The front rows kept circling back, as if the street had become a soft twist.",
            "A banner pole slipped from its holder and bent the line into a loop around the flower cart. The parade could still move, but only in a little circle that made everyone puzzled.",
        ],
        "conflict": [
            "\"We should stop it at once,\" said {infantry}. \"We should guide it through,\" said {sailor}. Their gentle disagreement left the parade waiting beside the flower cart.",
            "{sailor} pointed to the float. {infantry} pointed to the lanterns. Each had a kind idea, but the parade needed one clear choice before it could go on.",
        ],
        "turn": [
            "A grandmother handed them a warm bun and said, \"Try looking from the bench.\" After sharing the bun, they climbed the bench and saw the loop was only one crossed ribbon.",
            "The smell of fresh bread made the pair pause and breathe. When they looked again, they noticed the twist came from a single rope snagged on the wagon wheel.",
        ],
        "action": [
            "{sailor} lifted the ribbon, and {infantry} rolled the wagon back a step. Together they opened the path without upsetting a single flower.",
            "\"I see it now,\" said {sailor}. \"Then let's fix it kindly,\" answered {infantry}. They freed the rope, and the parade line straightened at once.",
        ],
        "resolution": [
            "The band played a cheerful tune, and the float rolled forward with no more circles. The parade thanked the two helpers by showering them with paper roses.",
            "Soon the street was open again, and the parade passed with shining lanterns and easy laughter. The twist had turned into a story everyone would remember fondly.",
        ],
        "ending": [
            "By sunset, the flower cart stood safely beside the road, and the last paper rose rested in {sailor}'s cap.",
            "The parade ended beneath the harbor lights, where the grateful crowd waved until the music faded into the evening air.",
        ],
        "problem_fact": "a crossed ribbon bent the parade into a little loop",
        "clue_fact": "looking from a bench showed the twist was only one snagged rope",
        "action_fact": "they freed the rope and rolled the wagon back",
        "outcome_fact": "the parade path opened and the music moved on",
    },
    {
        "premise": [
            "The {parade} was meant to welcome the sailors home, so {sailor} polished a silver whistle while infantry friend {infantry} stacked little flags by the curb.",
            "Children lined up for the {parade} as sailor {sailor} and infantry helper {infantry} set out water cups for anyone who grew tired in the sun.",
        ],
        "problem": [
            "When the band turned the corner, the front float pointed the wrong way and the parade began looping around the square. The cheerful crowd looked surprised by the sudden twist.",
            "A confetti storm made the map signs flutter, and the parade kept circling the same fountain. Each lap brought new smiles, but it also used up the marchers' energy.",
        ],
        "conflict": [
            "\"We can still follow it,\" said {sailor}. \"No, we must turn it around,\" said {infantry}. The two helpers paused, each trying to be right in a kind way.",
            "{infantry} reached for the signpost. {sailor} reached for the whistle. Their small conflict made the children wait, even though everyone wanted the parade to continue.",
        ],
        "turn": [
            "Then the mayor offered a cup of cocoa and asked them to sit for a breath. The break warmed their hands and helped them notice that the lead marcher was following the wrong drum.",
            "A little boy pointed and whispered, \"The drummer turned around.\" That simple clue, plus a shared drink of cocoa, gave them a better idea than either of them had alone.",
        ],
        "action": [
            "{sailor} called the true beat, and {infantry} turned the signpost to face it. Together they guided the lead marcher back into the right line.",
            "\"On my count,\" said {infantry}. \"And on mine,\" said {sailor}. They matched the drum and lifted the parade out of its loop one step at a time.",
        ],
        "resolution": [
            "The float rolled straight at last, and the parade flowed down the avenue like a bright ribbon. The helper's conflict ended in a shared smile.",
            "With the right beat restored, the crowd clapped in time and the parade became long and smooth again. The twist had led them to a better rhythm.",
        ],
        "ending": [
            "At the far end of the avenue, the sailors waved from the float while the infantry shared the last cocoa cup.",
            "The harbor bells rang softly as the parade disappeared beyond the bridge, straight and shining as promised.",
        ],
        "problem_fact": "the parade kept circling because the lead beat was turned around",
        "clue_fact": "a child noticed the drummer was facing the wrong way",
        "action_fact": "they turned the signpost and matched the true beat",
        "outcome_fact": "the parade found its straight route again",
    },
    {
        "premise": [
            "On a bright afternoon, sailor {sailor} joined infantry friend {infantry} in the town parade to carry a long friendship banner.",
            "The {parade} marched beside the river, where sailor {sailor} and infantry helper {infantry} handed out flowers from a basket and smiled at everyone they passed.",
        ],
        "problem": [
            "The banner snagged on a lamppost and twisted the front of the parade into a slow spinning turn. The line did not break, but it could not go where it wanted.",
            "A parade drum slipped from its strap and rolled in a circle near the curb. The marchers kept stepping around it, making the route feel like a soft knot.",
        ],
        "conflict": [
            "\"Let me yank it free,\" said {sailor}. \"Please don't,\" said {infantry}. Their voices stayed gentle, but both worried the parade would lose more time.",
            "{sailor} thought quick force would help. {infantry} thought careful hands would help more. Their conflict made the banner shake in the breeze.",
        ],
        "turn": [
            "A child brought them two warm biscuits, and they paused to share them. While chewing, they saw that the banner had wrapped around the pole in a neat little spiral.",
            "The biscuits were still warm from the bakery, and the comfort of the snack calmed their hurry. Then {infantry} spotted the spiral and nodded with relief.",
        ],
        "action": [
            "{infantry} held the banner still while {sailor} unwound one loop at a time. The spiral loosened without tearing the cloth.",
            "\"We can do this slowly,\" said {sailor}. {infantry} smiled. Together they lifted the banner up and slipped it over the lamppost top.",
        ],
        "resolution": [
            "The parade gave a happy cheer when the banner rose free. Soon the line moved on, straight and proud, with room for every marcher.",
            "Once the cloth was untwisted, the route opened like a path in a garden. The sailor and infantry walked side by side, relieved and warm-hearted.",
        ],
        "ending": [
            "At the river bridge, the friendship banner fluttered high above the parade, and the children clapped until their hands were pink.",
            "The last marcher passed under the lamplight, and the freed banner glowed like a ribbon of sunset.",
        ],
        "problem_fact": "the friendship banner twisted around a lamppost",
        "clue_fact": "sharing biscuits helped them notice the banner was spiraled",
        "action_fact": "they unwound the banner one loop at a time",
        "outcome_fact": "the parade line opened and moved on freely",
    },
]


def _render(template: str, sailor: Entity, infantry: Entity, parade: SceneState) -> str:
    return template.format(sailor=sailor.id, infantry=infantry.id, parade=parade.facts["parade_name"])


def tell(params: StoryParams) -> World:
    rng = _rng_for(params)
    arc = ARCS[(params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)]
    if params.seed is None:
        chosen = {k: rng.choice(v) for k, v in arc.items()}
    else:
        variant = (params.seed // len(ARCS)) % 8
        chosen = {k: v[(variant + i) % len(v)] for i, (k, v) in enumerate(arc.items())}
    state = SceneState(setting="the town square")
    world = World(state)
    sailor = world.add(Entity(id=params.sailor_name, kind="character", type="sailor", label="sailor"))
    infantry = world.add(Entity(id=params.infantry_name, kind="character", type="infantry", label="infantry"))
    parade = world.state
    parade.facts = {
        "sailor": sailor,
        "infantry": infantry,
        "parade_name": params.parade_name,
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
    }

    beats = ["premise", "problem", "conflict", "turn", "action", "resolution", "ending"]
    for i, beat in enumerate(beats):
        if i:
            world.para()
        world.say(_render(chosen[beat], sailor, infantry, parade))

    sailor.meters["energy"] = 3.0
    infantry.meters["energy"] = 3.0
    sailor.memes["worry"] = 0.0
    infantry.memes["worry"] = 0.0
    parade.parade_ready = True
    parade.twist_revealed = True
    parade.heart_full = True
    parade.crowd_smile = 1.0
    parade.band_playing = True
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.state.facts
    sailor = f["sailor"].id
    infantry = f["infantry"].id
    return [
        "Write a heartwarming parade story with a sailor and infantry helper who solve a twist together.",
        f"Tell a child-friendly story where {sailor} and {infantry} disagree kindly, then fix the parade route.",
        "Write a short story with a parade, a twist, and a warm ending that feels cheerful and gentle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.state.facts
    sailor = f["sailor"]
    infantry = f["infantry"]
    return [
        QAItem(
            question=f"Who were the two main helpers in the story?",
            answer=f"It was about {sailor.id}, a sailor, and {infantry.id}, an infantry helper, who worked together in the parade.",
        ),
        QAItem(
            question=f"What problem did the parade have?",
            answer=f["problem"],
        ),
        QAItem(
            question="What helped them notice what was really wrong?",
            answer=f["clue"],
        ),
        QAItem(
            question="How did they fix the parade?",
            answer=f"{f['action']} {f['outcome']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a happy procession of people moving together for a celebration.",
        ),
        QAItem(
            question="Who is a sailor?",
            answer="A sailor is a person who works on the water, often on a boat or ship.",
        ),
        QAItem(
            question="Who is infantry?",
            answer="Infantry are soldiers who travel and work on foot.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  parade_ready={world.state.parade_ready}")
    lines.append(f"  twist_revealed={world.state.twist_revealed}")
    lines.append(f"  heart_full={world.state.heart_full}")
    lines.append(f"  crowd_smile={world.state.crowd_smile}")
    lines.append(f"  band_playing={world.state.band_playing}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(parade, sailor, infantry, twist, heartwarming) :-
    parade_theme, sailor_theme, infantry_theme, twist_theme, heart_theme.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("parade_theme"),
            asp.fact("sailor_theme"),
            asp.fact("infantry_theme"),
            asp.fact("twist_theme"),
            asp.fact("heart_theme"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/5."))
    if any(sym.name == "valid_story" for sym in model):
        sample = generate(StoryParams("Mina", "Owen", "Lantern Parade", seed=7))
        if sample.story and "“" not in sample.story:
            print("OK: ASP twin recognizes the parade sailor infantry twist story.")
            return 0
    print("MISMATCH: ASP twin did not recognize the expected story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming parade world with sailor, infantry, and a twist.")
    ap.add_argument("--sailor-name")
    ap.add_argument("--infantry-name")
    ap.add_argument("--parade-name", choices=PARADE_NAMES)
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
    sailor = args.sailor_name or rng.choice(NAMES)
    infantry = args.infantry_name or rng.choice([n for n in NAMES if n != sailor])
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
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible heartwarming parade pattern: sailor + infantry + twist + resolution")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mina", "Owen", "Lantern Parade"),
            StoryParams("Lena", "Toby", "Ribbon Parade"),
            StoryParams("June", "Nico", "Harbor Parade"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
