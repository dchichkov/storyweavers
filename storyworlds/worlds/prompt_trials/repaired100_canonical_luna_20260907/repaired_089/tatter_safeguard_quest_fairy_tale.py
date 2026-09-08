#!/usr/bin/env python3
"""
Storyworld: tatter_safeguard_quest_fairy_tale

A small fairy-tale world about a tattered banner, a protective safeguard,
and a quest that succeeds through patience rather than reckless magic.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    name: str
    kind: str
    role: str
    home: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(
        default_factory=lambda: {"danger": 0.0, "distance": 0.0, "readiness": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"worry": 0.0, "hope": 0.0, "trust": 0.0}
    )


@dataclass
class Relic:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(
        default_factory=lambda: {"fragility": 0.0, "safety": 0.0, "magic": 0.0}
    )


@dataclass
class StoryParams:
    hero_name: str
    guardian_name: str
    companion_name: str
    kingdom: str
    destination: str
    tatter: str
    safeguard: str
    quest: str
    telling_mode: str = "dawn"
    seed: Optional[int] = None


KINGDOMS = {
    "Moonmere": {
        "homes": ["the moonlit village", "the silver reed marsh"],
        "destinations": ["the Bell Tower of Dawn", "the Lantern Hill"],
        "tatter": "a tattered royal banner",
        "safeguard": "a ring of blue warding thread",
    },
    "Rosevale": {
        "homes": ["the rose-gate village", "the greenwood cottage"],
        "destinations": ["the Sleeping Rose Palace", "the Thornbridge"],
        "tatter": "a tattered cloak of stars",
        "safeguard": "a silver thimble of protection",
    },
    "Emberfall": {
        "homes": ["the warm valley hamlet", "the ash-tree farm"],
        "destinations": ["the Dragon's Quiet Cave", "the Hearthstone Gate"],
        "tatter": "a tattered map of ember roads",
        "safeguard": "a brass compass shield",
    },
    "Willowmere": {
        "homes": ["the willow village", "the riverbank mill"],
        "destinations": ["the Whispering Isle", "the Old Willow Crown"],
        "tatter": "a tattered ribbon of river silk",
        "safeguard": "a woven reed bracelet",
    },
}

HERO_NAMES = ["Luna", "Elian", "Mara", "Pip", "Nell", "Tobin"]
GUARDIAN_NAMES = ["Aster", "Brindle", "Sorrel", "Moss", "Iris", "Rowan"]
COMPANION_NAMES = ["Moth", "Pipkin", "Thistle", "Clover", "Wren", "Bramble"]

QUESTS = {
    "fallen star": {
        "premise": "a small fallen star had gone dark beside the road",
        "impulse": "pick up the star and carry it straight through the forbidden thorns",
        "warning": "A bright thing may still be hot. We must learn its secret before we lift it",
        "clue": "the star's dim light brightened whenever the tattered cloth was held near it",
        "mistake": "the star was not waiting for a strong hand; it was waiting for a safe shelter",
        "safe_action": "stretched the tattered cloth between two hazel branches, placed the safeguard around the shelter, and asked the moon-mage for guidance",
        "result": "the star cooled inside the protected cloth and rose again when the moon-mage spoke the old road's true name",
        "lesson": "a quest is made wiser by protection and careful questions",
        "ending": "the once-dark star shone above the path, and its gentle light led lost travelers home",
    },
    "sleeping dragon": {
        "premise": "a young dragon slept across the only bridge to the mountain castle",
        "impulse": "sneak past its wings before it woke",
        "warning": "A sleeping dragon is still a dragon. No quest is worth stepping into a creature's danger",
        "clue": "one golden scale trembled whenever the tattered cloak caught the wind",
        "mistake": "the dragon was dreaming of the cloak's old song, not guarding the bridge by accident",
        "safe_action": "stood behind the safeguard stones, played the cloak's melody from a distance, and waited for the dragon to open one sleepy eye",
        "result": "the dragon woke peacefully, listened to the quest, and carried the travelers over the bridge on its broad back",
        "lesson": "respect can open a path that courage alone cannot",
        "ending": "At sunset, the dragon curled beside the bridge while the tattered cloak fluttered like a friendly flag",
    },
    "glass orchard": {
        "premise": "the orchard of glass apples had lost its keeper's bell",
        "impulse": "climb the glittering trees and search among the sharp branches",
        "warning": "Beauty can cut as quickly as a sword. We need a safeguard before entering the orchard",
        "clue": "a single apple rang softly whenever the tatter brushed the gate",
        "mistake": "the missing bell was hidden by a sound, not by a branch",
        "safe_action": "wrapped the safeguard around the gate latch, followed the ringing from outside, and asked the orchard sprites to answer",
        "result": "the sprites returned the bell from beneath a root, and the glass apples stopped trembling",
        "lesson": "listening from a safe place can reveal what rushing would break",
        "ending": "The restored bell chimed, and rainbow light spilled over fruit that no longer shook",
    },
    "river of ink": {
        "premise": "a river of black ink had swallowed the bridge stones",
        "impulse": "wade into the ink and pull the stones back by hand",
        "warning": "Ink can hide a deep current. Our safeguard must reach the water before any foot does",
        "clue": "the tattered map showed a forgotten dry crossing beneath the willow bank",
        "mistake": "the bridge stones were not gone; the river had changed its course around them",
        "safe_action": "tied the safeguard to a long branch, tested the hidden crossing from the bank, and followed the map's dotted line",
        "result": "the questers crossed safely and placed white stones along the dry route for others",
        "lesson": "an old clue may become a safeguard when the world changes",
        "ending": "Moonlight touched the white stones, making a safe road through the river's dark shine",
    },
    "thorn crown": {
        "premise": "a thorn crown lay in the center of a clearing where wishes came true",
        "impulse": "grab the crown before another traveler could claim its wishes",
        "warning": "A wish taken in haste may grow thorns around the wisher. Let us protect our hands and our hearts",
        "clue": "the tatter fluttered toward the crown only when no one spoke of wanting it",
        "mistake": "the crown answered generosity, not grabbing",
        "safe_action": "set the safeguard in a circle, spoke a wish for the forest's healing, and waited without touching the crown",
        "result": "the thorns opened, revealing a plain wooden key meant for the locked village well",
        "lesson": "a quest becomes noble when its prize helps more than one traveler",
        "ending": "The key opened the well, and clear water rose beneath the crown's quiet flowers",
    },
    "whispering tower": {
        "premise": "a lonely tower whispered the name of every traveler who came near",
        "impulse": "run inside and climb until the tower revealed its secret",
        "warning": "A whisper can guide or lure. We need a safeguard and a companion before climbing",
        "clue": "the tower repeated the name of the tattered cloth instead of the hero's name",
        "mistake": "the tower was calling the lost banner home, not calling the traveler inside",
        "safe_action": "anchored the safeguard at the doorway, asked the companion to remember the path, and held the tatter where the whisper could hear",
        "result": "the tower opened a low side door and returned the banner's missing golden thread",
        "lesson": "a careful companion can turn a frightening mystery into a useful conversation",
        "ending": "The tower grew quiet, and its new golden thread gleamed in the dawn",
    },
    "frost garden": {
        "premise": "a frost garden had frozen the path to the queen's sick garden",
        "impulse": "break the ice roses with a staff",
        "warning": "Breaking the spell may break the sleeping flowers. We must protect the garden before touching it",
        "clue": "the tattered ribbon warmed one small patch of soil",
        "mistake": "the garden needed a gentle memory, not a strong blow",
        "safe_action": "laid the safeguard around the warm patch, told the story woven into the ribbon, and waited for the roots to listen",
        "result": "the frost melted in a winding path, leaving every ice rose whole",
        "lesson": "gentleness can be the strongest magic on a healing quest",
        "ending": "The queen's garden bloomed beneath the thawing sky, with one frost rose saved in a glass cup",
    },
    "candle cavern": {
        "premise": "a cave of endless candles held the last flame for the kingdom's winter lamps",
        "impulse": "dash into the cave and seize the brightest candle",
        "warning": "A cave has its own darkness. Carry a safeguard, mark the path, and never chase a flame",
        "clue": "the tattered map showed that the brightest candle was a false reflection",
        "mistake": "the true flame burned quietly beside the entrance, where careless eyes ignored it",
        "safe_action": "marked each turn with harmless chalk, kept the safeguard between the travelers and the deep shadows, and chose the quiet flame",
        "result": "the last flame stayed lit as it was carried home in a covered lantern",
        "lesson": "the right treasure may be modest, steady, and close at hand",
        "ending": "Warm lamps glowed in every window while the cave kept its patient golden hush",
    },
}

TELLING_MODES = (
    "dawn",
    "warning-first",
    "prophecy",
    "road",
    "dialogue-first",
    "storm",
    "festival",
    "quiet",
)

REASONING_BEATS = (
    '{hero} studied the road and said, "A quest needs more than brave feet. It needs a way to keep everyone safe."',
    "{guardian} asked {hero} to name the danger, the safeguard, and the person who might know more. The three answers made the next step clear.",
    "{companion} drew a little circle around the risky place. Inside the circle was what they could not yet understand; outside it was where they could plan.",
    '{hero} took three slow breaths. "If I hurry, I may win a moment and lose the whole quest," the traveler said.',
    "The companions compared what they knew with what they guessed. The dangerous idea belonged in the guessing pile.",
    '{guardian} pointed to the tatter and said, "Old things can carry clues, but a clue is not permission to rush."',
    "{hero} imagined the quest failing through haste, then imagined it succeeding through patience. The second picture showed a kinder road.",
)

CLOSING_EXCHANGES = (
    '"You carried the safeguard before the prize," {guardian} said. "That is why the prize could be carried at all."',
    '"The quest changed when we listened," {hero} said. {companion} nodded, and the road seemed less lonely.',
    '"Courage kept us walking," said {companion}, "but care kept us together."',
    '{hero} thanked {guardian} for the warning. "A warning is a lantern," the traveler said, "not a wall."',
    "{guardian} invited the companions to teach the next travelers where the safe path began.",
)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.characters: dict[str, Character] = {}
        self.relics: dict[str, Relic] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append(" ".join(current))
        return "\n\n".join(paragraphs)


def build_world(params: StoryParams) -> World:
    if params.kingdom not in KINGDOMS:
        raise StoryError(f"Unknown kingdom: {params.kingdom}")
    if params.quest not in QUESTS:
        raise StoryError(f"Unknown quest: {params.quest}")
    if not params.hero_name.strip() or not params.guardian_name.strip() or not params.companion_name.strip():
        raise StoryError("Character names must not be empty")

    world = World(params)
    quest = QUESTS[params.quest]

    hero = Character(
        "hero",
        params.hero_name,
        "human",
        "quester",
        params.kingdom,
        ["curious", "brave", "learning patience"],
    )
    guardian = Character(
        "guardian",
        params.guardian_name,
        "human",
        "wise guardian",
        params.kingdom,
        ["watchful", "kind", "firm"],
    )
    companion = Character(
        "companion",
        params.companion_name,
        "fairy companion",
        "quest companion",
        params.kingdom,
        ["small", "observant", "loyal"],
    )
    tatter = Relic("tatter", params.tatter, "old enchanted cloth", owner=hero.id)
    safeguard = Relic("safeguard", params.safeguard, "protective charm", owner=guardian.id)

    world.characters.update(
        hero=hero,
        guardian=guardian,
        companion=companion,
    )
    world.relics.update(tatter=tatter, safeguard=safeguard)

    openings = {
        "dawn": f"At dawn in {params.kingdom}, {hero.name} discovered that {quest['premise']} near {params.destination}.",
        "warning-first": f'"Stay by the lantern stones," called {guardian.name}. In {params.kingdom}, {quest["premise"]} near {params.destination}.',
        "prophecy": f"An old prophecy said that {quest['premise']} near {params.destination}, and that only a patient quester could mend the trouble.",
        "road": f"Along the road from {params.kingdom}, {hero.name} saw that {quest['premise']} near {params.destination}.",
        "dialogue-first": f'"I will solve this before sunset," said {hero.name}, after learning that {quest["premise"]} near {params.destination}.',
        "storm": f"After a storm crossed {params.kingdom}, {quest['premise']} near {params.destination}, and the wet road glittered with trouble.",
        "festival": f"While bells rang for the spring festival in {params.kingdom}, word spread that {quest['premise']} near {params.destination}.",
        "quiet": f"The morning was quiet in {params.kingdom} when {hero.name} heard that {quest['premise']} near {params.destination}.",
    }
    world.say(openings[params.telling_mode])
    world.say(
        f"{hero.name} carried {params.tatter}, a tatter saved from an older adventure, while "
        f"{guardian.name} kept {params.safeguard} wrapped in a blue cloth."
    )
    world.say(f"The first impulse of the young quester was to {quest['impulse']}.")
    hero.meters["danger"] += 1
    tatter.meters["fragility"] += 1
    world.para()

    world.say(
        f'{guardian.name} raised a hand and gave a clear warning: "{quest["warning"]}."'
    )
    world.say(
        f"The danger was not only the path itself. {quest['mistake']}, so a hurried choice "
        f"could harm the quest and anyone following it."
    )
    beat_rng = random.Random((params.seed or 0) ^ 0x71A77E)
    world.say(
        beat_rng.choice(REASONING_BEATS).format(
            hero=hero.name,
            guardian=guardian.name,
            companion=companion.name,
        )
    )
    guardian.memes["worry"] += 1
    hero.memes["hope"] += 1
    world.para()

    world.say(
        f"Then {companion.name} noticed the useful clue: {quest['clue']}."
    )
    world.say(
        f'"I thought a quest meant reaching the prize first," {hero.name} admitted. '
        f'"Now I think it means bringing everyone safely to the truth."'
    )
    world.say(
        f"With {guardian.name} watching and {companion.name} beside the road, "
        f"{hero.name} {quest['safe_action']}."
    )
    hero.meters["distance"] += 1
    hero.meters["readiness"] += 1
    safeguard.meters["safety"] += 1
    safeguard.meters["magic"] += 1
    companion.memes["trust"] += 1
    world.para()

    world.say(f"The careful plan worked: {quest['result']}.")
    world.say(
        f"The tatter was not thrown away. It was folded beside the safeguard and kept as a "
        f"reminder that old, torn things can still protect a new beginning."
    )
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    guardian.memes["trust"] += 1
    world.say(f"{hero.name} learned that {quest['lesson']}.")
    closing_rng = random.Random((params.seed or 0) ^ 0xC0FFEE)
    world.say(
        closing_rng.choice(CLOSING_EXCHANGES).format(
            hero=hero.name,
            guardian=guardian.name,
            companion=companion.name,
        )
    )
    world.say(f"{quest['ending']}.")

    world.facts.update(
        hero=hero,
        guardian=guardian,
        companion=companion,
        tatter=tatter,
        safeguard=safeguard,
        quest_name=params.quest,
        premise=quest["premise"],
        impulse=quest["impulse"],
        warning=quest["warning"],
        clue=quest["clue"],
        mistaken_belief=quest["mistake"],
        safe_action=quest["safe_action"],
        result=quest["result"],
        lesson=quest["lesson"],
        ending=quest["ending"],
        destination=params.destination,
        kingdom=params.kingdom,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Character = f["hero"]
    tatter: Relic = f["tatter"]
    return [
        f"Write a fairy tale about {hero.name}'s Quest to solve {f['premise']}.",
        f"Tell a story in which {hero.name} carries {tatter.label}, discovers {f['clue']}, and uses a safeguard instead of rushing into danger.",
        f"Write a child-friendly fairy tale showing that {hero.name} learns {f['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Character = f["hero"]
    guardian: Character = f["guardian"]
    tatter: Relic = f["tatter"]
    safeguard: Relic = f["safeguard"]

    return [
        QAItem(
            question=f"What did {hero.name} first want to do on the Quest?",
            answer=f"{hero.name} first wanted to {f['impulse']}. That choice was risky because {f['mistaken_belief'].lower()}",
        ),
        QAItem(
            question=f"What clue changed {hero.name}'s plan?",
            answer=f"{hero.name} learned that {f['clue']}. The clue showed that the quest needed observation rather than a hurried action.",
        ),
        QAItem(
            question=f"How did {hero.name} use the safeguard?",
            answer=f"{hero.name} used {safeguard.label} while {f['safe_action']}. The safeguard kept the questers protected while they solved the mystery.",
        ),
        QAItem(
            question=f"Why was {guardian.name}'s warning important?",
            answer=f"{guardian.name}'s warning was important because {f['warning'].rstrip('.')}. It stopped the quest from becoming an unnecessary danger.",
        ),
        QAItem(
            question="What final image proves that the Quest succeeded?",
            answer=f"The final image is this: {f['ending']}. It shows the safe result instead of merely saying that everything ended well.",
        ),
        QAItem(
            question=f"What happened to the tatter?",
            answer=f"The tatter was folded beside the safeguard and kept as a reminder that old, torn things can still protect a new beginning.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey undertaken to solve a problem, find something important, or help someone.",
        ),
        QAItem(
            question="What is a safeguard?",
            answer="A safeguard is something that protects people or keeps a plan from becoming dangerous.",
        ),
        QAItem(
            question="What does tatter mean?",
            answer="A tatter is a torn or ragged piece of cloth.",
        ),
        QAItem(
            question="What makes a fairy tale?",
            answer="A fairy tale often includes wonder, enchanted objects, talking creatures, brave choices, and a lesson learned through adventure.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for character in world.characters.values():
        lines.append(
            f"{character.id}: kind={character.kind} role={character.role} "
            f"meters={dict(character.meters)} memes={dict(character.memes)}"
        )
    for relic in world.relics.values():
        lines.append(
            f"{relic.id}: label={relic.label} kind={relic.kind} "
            f"owner={relic.owner} meters={dict(relic.meters)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
% The fairy-tale quest is reasonable when danger is met with protection and patience.
successful_quest(S) :-
    story(S),
    quest(S),
    tatter_clue(S),
    safeguard_used(S),
    patient_choice(S).

quest(S) :- story(S), seeks_answer(S).
tatter_clue(S) :- story(S), old_cloth_reveals(S).
safeguard_used(S) :- story(S), protection_ready(S).
patient_choice(S) :- story(S), refuses_rush(S).
"""


def asp_facts(params: StoryParams) -> str:
    import asp

    return "\n".join(
        [
            asp.fact("story", "s1"),
            asp.fact("seeks_answer", "s1"),
            asp.fact("old_cloth_reveals", "s1"),
            asp.fact("protection_ready", "s1"),
            asp.fact("refuses_rush", "s1"),
        ]
    )


def asp_program() -> str:
    params = StoryParams(
        hero_name="Luna",
        guardian_name="Aster",
        companion_name="Moth",
        kingdom="Moonmere",
        destination="the Bell Tower of Dawn",
        tatter="a tattered royal banner",
        safeguard="a ring of blue warding thread",
        quest="fallen star",
    )
    return f"{asp_facts(params)}\n{ASP_RULES}\n#show successful_quest/1.\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "successful_quest"))
    if found != {("s1",)}:
        print("MISMATCH: ASP did not recognize the safeguarded quest.")
        return 1

    sample = generate(
        StoryParams(
            hero_name="Luna",
            guardian_name="Aster",
            companion_name="Moth",
            kingdom="Moonmere",
            destination="the Bell Tower of Dawn",
            tatter="a tattered royal banner",
            safeguard="a ring of blue warding thread",
            quest="fallen star",
            seed=17,
        )
    )
    required = ("tattered", "safeguard", "quest")
    if not all(word in sample.story.lower() for word in required):
        print("MISMATCH: generated story is missing required narrative language.")
        return 1
    if len(sample.story_qa) < 4:
        print("MISMATCH: generated story lacks grounded QA.")
        return 1

    print("OK: ASP gate matches the safeguarded quest and generated stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fairy-tale world about a tatter, a safeguard, and a careful quest."
    )
    parser.add_argument("--hero-name")
    parser.add_argument("--guardian-name")
    parser.add_argument("--companion-name")
    parser.add_argument("--kingdom", choices=sorted(KINGDOMS))
    parser.add_argument("--destination")
    parser.add_argument("--quest", choices=sorted(QUESTS))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    kingdom = args.kingdom or rng.choice(sorted(KINGDOMS))
    config = KINGDOMS[kingdom]
    destination = args.destination or rng.choice(config["destinations"])
    quest_name = args.quest or rng.choice(sorted(QUESTS))

    return StoryParams(
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        guardian_name=args.guardian_name or rng.choice(GUARDIAN_NAMES),
        companion_name=args.companion_name or rng.choice(COMPANION_NAMES),
        kingdom=kingdom,
        destination=destination,
        tatter=config["tatter"],
        safeguard=config["safeguard"],
        quest=quest_name,
        telling_mode=rng.choice(TELLING_MODES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


CURATED = [
    StoryParams(
        hero_name="Luna",
        guardian_name="Aster",
        companion_name="Moth",
        kingdom="Moonmere",
        destination="the Bell Tower of Dawn",
        tatter="a tattered royal banner",
        safeguard="a ring of blue warding thread",
        quest="fallen star",
        telling_mode="dawn",
        seed=101,
    ),
    StoryParams(
        hero_name="Mara",
        guardian_name="Sorrel",
        companion_name="Thistle",
        kingdom="Rosevale",
        destination="the Thornbridge",
        tatter="a tattered cloak of stars",
        safeguard="a silver thimble of protection",
        quest="sleeping dragon",
        telling_mode="road",
        seed=202,
    ),
    StoryParams(
        hero_name="Elian",
        guardian_name="Rowan",
        companion_name="Wren",
        kingdom="Willowmere",
        destination="the Whispering Isle",
        tatter="a tattered ribbon of river silk",
        safeguard="a woven reed bracelet",
        quest="river of ink",
        telling_mode="quiet",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        print(asp.one_model(asp_program()))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
