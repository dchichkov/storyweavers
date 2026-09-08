#!/usr/bin/env python3
"""A heartwarming parade world with a sailor, infantry, and a gentle twist."""

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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    mood: str
    weather: str


@dataclass
class StoryParams:
    setting: str = ""
    parade: str = ""
    sailor: str = ""
    infantry: str = ""
    twist: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class ParadeBeat:
    opening: str
    tension: str
    turn: str
    ending: str
    dialogue: tuple[str, str]


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "harbor": Scene("the harbor", "bright", "salt wind"),
    "square": Scene("the square", "lively", "soft morning sun"),
    "hill": Scene("the hill", "open", "a clear blue breeze"),
}

PARADES = {
    "lantern parade": "a lantern parade for the whole town",
    "flower parade": "a flower parade with ribbons and drums",
    "homecoming parade": "a homecoming parade for returning neighbors",
    "harvest parade": "a harvest parade with wheeled carts and songs",
}

SAILORS = {
    "Mara": "girl",
    "Eli": "boy",
    "June": "girl",
    "Noah": "boy",
}

INFANTRY = {
    "Captain Reed's infantry": "soldiers",
    "the marching infantry": "soldiers",
    "the town infantry": "soldiers",
    "the hill infantry": "soldiers",
}

TWISTS = {
    "lost banner": ParadeBeat(
        opening="A parade was about to begin, but one bright banner was missing from the front cart.",
        tension="People worried the opening song could not start without the parade colors.",
        turn="The sailor found the banner folded inside a rain barrel, where it had been tucked to keep it dry.",
        ending="The parade rolled on with the rescued banner fluttering over smiling faces.",
        dialogue=("\"I can climb up and look,\" the sailor said.", "\"Please do,\" answered the infantry leader, \"and we will wait together.\""),
    ),
    "shy drummer": ParadeBeat(
        opening="The parade drumline was ready, but one young drummer hid behind a wagon wheel.",
        tension="The infantry waited in a neat row, and the music felt too quiet to march with.",
        turn="The sailor sat beside the drummer and said, \"I can count the beat with you.\" The child smiled and stepped forward.",
        ending="Soon the whole parade moved in time, and the shy drummer grinned at the cheering crowd.",
        dialogue=("\"I am nervous,\" the drummer whispered.", "\"Then we will be brave slowly,\" said the sailor."),
    ),
    "heavy crate": ParadeBeat(
        opening="A heavy crate blocked the parade route near the harbor gate.",
        tension="The infantry could not push it alone, and the crowd began to worry.",
        turn="The sailor noticed the crate was full of donated blankets, so the soldiers and townsfolk carried the blankets first and lifted the empty crate after.",
        ending="By helping each other, they cleared the road and turned the parade into a warm sharing feast.",
        dialogue=("\"That crate is too heavy,\" said one soldier.", "\"Only when it is full,\" the sailor replied, \"so let us share what is inside.\""),
    ),
    "missing music": ParadeBeat(
        opening="At dawn, the parade lost its music when the fiddle player could not be found.",
        tension="The infantry marched in silence, and the silence made every step feel lonely.",
        turn="The sailor followed a soft humming sound to the bakery window, where the fiddle player was helping a child reach a warm loaf.",
        ending="The music returned, and the parade sounded even kinder than before because everyone had waited.",
        dialogue=("\"I thought you had run away,\" said the captain.", "\"No,\" the fiddler answered, \"I was helping someone small.\""),
    ),
    "rainy turn": ParadeBeat(
        opening="Dark clouds rolled in just as the parade lined up beneath the flags.",
        tension="The crowd feared the rain would send everyone home before the first wave.",
        turn="The sailor tied tarps between the carts while the infantry held umbrellas high, making a shining tunnel for the children.",
        ending="The parade became a rainy-day joy instead of a disappointment, and the town laughed under every splash.",
        dialogue=("\"The rain is winning,\" said a child.", "\"Not today,\" the sailor said, \"we know how to march under a sky like this.\""),
    ),
}

ROUTES = ("opening_first", "dialogue_first", "test_first", "crowd_first", "quiet_first", "weather_first", "helper_first", "twist_first")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming parade story world with a sailor and infantry.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--parade", choices=sorted(PARADES))
    ap.add_argument("--sailor", choices=sorted(SAILORS))
    ap.add_argument("--infantry", choices=sorted(INFANTRY))
    ap.add_argument("--twist", choices=sorted(TWISTS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    return [
        (setting, parade, sailor, infantry, twist)
        for setting in sorted(SETTINGS)
        for parade in sorted(PARADES)
        for sailor in sorted(SAILORS)
        for infantry in sorted(INFANTRY)
        for twist in sorted(TWISTS)
    ]


ASP_RULES = """
valid(S, P, Sa, I, T) :- setting(S), parade(P), sailor(Sa), infantry(I), twist(T).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            *(asp.fact("setting", s) for s in SETTINGS),
            *(asp.fact("parade", p) for p in PARADES),
            *(asp.fact("sailor", s) for s in SAILORS),
            *(asp.fact("infantry", i) for i in INFANTRY),
            *(asp.fact("twist", t) for t in TWISTS),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid/5.")), "valid")))


def asp_verify() -> int:
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:", sorted(py - cl), sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c
        for c in valid_combos()
        if (not args.setting or c[0] == args.setting)
        and (not args.parade or c[1] == args.parade)
        and (not args.sailor or c[2] == args.sailor)
        and (not args.infantry or c[3] == args.infantry)
        and (not args.twist or c[4] == args.twist)
    ]
    if not combos:
        raise StoryError("No valid parade story fits those options.")
    setting, parade, sailor, infantry, twist = rng.choice(combos)
    return StoryParams(setting=setting, parade=parade, sailor=sailor, infantry=infantry, twist=twist)


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(x) for x in (params.seed, params.setting, params.parade, params.sailor, params.infantry, params.twist))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = SETTINGS[params.setting]
    beat = TWISTS[params.twist]
    rng = story_rng(params)
    world = World(scene)

    sailor = world.add(Entity(id=params.sailor, kind="character", type=SAILORS[params.sailor], label="sailor"))
    infantry = world.add(Entity(id=params.infantry, kind="group", type=INFANTRY[params.infantry], label="infantry"))
    parade = world.add(Entity(id=params.parade, kind="event", type="parade", label=params.parade))

    sailor.meters["help_steps"] = 0
    sailor.memes["kindness"] = 1
    infantry.memes["teamwork"] = 1
    parade.meters["joy"] = 1

    openings = {
        "opening_first": f"At {scene.place}, {params.parade} was ready to begin. The morning felt {scene.mood}, but something important was missing.",
        "dialogue_first": f"\"Hold on,\" said {params.sailor}. The parade was lining up at {scene.place}, and the infantry was waiting for the first signal.",
        "test_first": f"{params.sailor} liked to test every parade plan twice. Today, the test happened at {scene.place} before {params.parade} could start.",
        "crowd_first": f"The crowd gathered early at {scene.place} for {params.parade}, and the infantry stood nearby with polished boots and patient smiles.",
        "quiet_first": f"Before the music started, {scene.place} felt very quiet. Then {params.sailor} noticed the infantry watching an empty spot in the line.",
        "weather_first": f"The sky over {scene.place} was full of movement, and {params.parade} seemed ready for a surprise.",
        "helper_first": f"{params.sailor} came to help the infantry prepare for {params.parade}. It was the kind of day when small kindnesses mattered most.",
        "twist_first": f"The surprise came early at {scene.place}: the parade had a twist before anyone expected one.",
    }
    world.say(openings[params.setting if params.setting in openings else "opening_first"])
    world.say(rng.choice([
        f"The sailor waved to the infantry and said, \"We can solve this together.\"",
        f"The infantry leader replied, \"Good. A parade is better when every helper has a place.\"",
        f"Children along the road listened as {params.sailor} promised, \"No one gets left behind today.\"",
    ]))
    world.para()
    world.say(beat.opening)
    world.say(rng.choice([
        f"{params.sailor} checked the carts, the ropes, and the flags with careful hands.",
        f"The infantry kept the line steady so the crowd would not worry.",
        f"Everyone paused long enough to notice what the parade needed most.",
    ]))
    world.say(beat.tension)
    world.say(beat.dialogue[0])
    world.say(beat.dialogue[1])
    world.para()
    world.say(beat.turn)
    world.say(rng.choice([
        f"That small change softened the whole scene, and even the infantry relaxed their shoulders.",
        f"The answer was not grand; it was thoughtful, which made it feel warmer.",
        f"Once they understood the problem, the sailor and infantry moved like one team.",
    ]))
    sailor.meters["help_steps"] += 2
    parade.memes["warm"] = 2
    world.say(rng.choice([
        f"The sailor tipped a hat to the infantry, and the infantry answered with a proud smile.",
        f"A child clapped first, then the whole street joined in.",
        f"Neighbors began offering extra hands, cups of water, and kind words.",
    ]))
    world.para()
    world.say(f"In the end, {beat.ending}")
    world.say(rng.choice([
        f"{params.sailor} watched the parade pass and felt glad that helping had become the best part of the day.",
        f"The infantry marched on with lighter steps because the trouble had turned into care.",
        f"The town remembered not just the parade, but the kindness that kept it moving.",
    ]))

    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        parade=parade,
        scene=scene,
        beat=beat,
        twist=params.twist,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story about {f['sailor'].id}, {f['infantry'].label}, and {f['parade'].label} at {f['scene'].place}.",
        f"Tell a child-friendly parade tale with a small twist that turns worry into teamwork.",
        f"Write a warm story where a sailor and an infantry group help each other finish a parade happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    beat: ParadeBeat = f["beat"]
    return [
        QAItem(
            question=f"What kind of event was happening at {f['scene'].place}?",
            answer=f"It was a parade, and everyone was getting ready to share it with the town.",
        ),
        QAItem(
            question=f"Who helped the infantry during the trouble?",
            answer=f"{f['sailor'].id} helped the infantry by looking closely, speaking kindly, and finding a good way forward.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=beat.turn,
        ),
        QAItem(
            question=f"How did the ending show that things turned out well?",
            answer=beat.ending,
        ),
        QAItem(
            question="What changed between the beginning and the end?",
            answer="The parade began with worry, but it ended with teamwork, relief, and cheerful smiles.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a cheerful procession where people move together along a route, often with music, flags, or costumes.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or around water and is often good at steady hands, ropes, and careful teamwork.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry means soldiers who travel and work on foot, usually in a group with discipline and teamwork.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)), "", "== story qa =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.kind}/{e.type}) meters={e.meters} memes={e.memes}")
    lines.append(f"  scene={world.facts['scene'].place} mood={world.facts['scene'].mood}")
    lines.append(f"  twist={world.facts['twist']}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(setting="harbor", parade="lantern parade", sailor="Mara", infantry="Captain Reed's infantry", twist="lost banner", seed=11),
    StoryParams(setting="square", parade="homecoming parade", sailor="Eli", infantry="the town infantry", twist="shy drummer", seed=22),
    StoryParams(setting="hill", parade="flower parade", sailor="June", infantry="the marching infantry", twist="rainy turn", seed=33),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for setting, parade, sailor, infantry, twist in combos:
            print(f"  {setting:8} {parade:18} {sailor:8} {infantry:24} {twist}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples, seen, attempts = [], set(), 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header="### curated story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else ""),
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
