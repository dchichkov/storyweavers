#!/usr/bin/env python3
"""
storyworlds/worlds/twinkling_path_whispering_fox_forest_trail_cautionary.py
============================================================================

Seed prompt
-----------
Write a story that includes the following words and narrative instruments.
Words: twinkling path, whispering fox
Setting: forest trail
Features: Cautionary, Sharing
Style: Fable

Source tale written from the seed
---------------------------------
On a forest trail, a young animal and a smaller companion see a twinkling path
that looks like an easy shortcut home. A whispering fox slinks beside the ferns
and gives selfish advice: hurry, keep the useful thing for yourself, and let the
slower friend manage alone.

The warning hidden inside the tale is simple: bright temptation and sly advice
are not the same as wisdom. The safe path only becomes clear when the traveler
shares what they are carrying. Shared light reveals dry roots, shared berries
slow a hungry friend enough to notice the open gap, and a shared vine loop lets
two walkers cross together instead of alone. The ending image should prove the
change: the fox is left whispering to himself while the friends move forward in
step.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class HeroSpec:
    id: str
    label: str
    kind: str
    trait: str
    carries: set[int]
    home: str
    caution_voice: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class TrailSpec:
    id: str
    name: str
    opening: str
    twinkle_source: str
    hazard: str
    need_aid: str
    fox_lure: str
    warning_line: str
    safe_detail: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ShareSpec:
    id: str
    label: str
    phrase: str
    size: int
    aid: str
    comfort: str
    material: str
    share_action: str
    reveal_action: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class CompanionSpec:
    id: str
    label: str
    kind: str
    need: str
    problem: str
    thanks: str
    pace: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    hero: str
    trail: str
    share: str
    companion: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    type: str
    meters: dict[str, int] = field(default_factory=dict)
    memes: dict[str, int] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    actor: str
    place: str
    text: str
    target: Optional[str] = None


@dataclass
class StoryWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event_id: str, actor: str, place: str, text: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, actor, place, text, target))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(parts) for parts in self.paragraphs if parts)


HEROES = {
    "rowan_rabbit": HeroSpec(
        id="rowan_rabbit",
        label="Rowan Rabbit",
        kind="rabbit",
        trait="quick-footed",
        carries={1, 2},
        home="the hazelnut burrow at the end of the trail",
        caution_voice="Quick feet should still listen to slow wisdom.",
        tags={"forest", "sharing", "caution"},
    ),
    "bramble_badger": HeroSpec(
        id="bramble_badger",
        label="Bramble Badger",
        kind="badger",
        trait="broad-backed",
        carries={1, 2},
        home="the mossy den beyond the oaks",
        caution_voice="Strong paws are safest when they carry others kindly.",
        tags={"forest", "sharing", "caution"},
    ),
    "pippa_squirrel": HeroSpec(
        id="pippa_squirrel",
        label="Pippa Squirrel",
        kind="squirrel",
        trait="bright-eyed",
        carries={1},
        home="the hollow cedar near the trail bend",
        caution_voice="A bright mind should not be stolen by bright tricks.",
        tags={"forest", "sharing", "caution"},
    ),
}

TRAILS = {
    "glimmer_roots": TrailSpec(
        id="glimmer_roots",
        name="Glimmer Roots",
        opening="At Glimmer Roots, the forest trail ran under fir branches where dusk came early.",
        twinkle_source="dew on pale roots made a twinkling path under the needles",
        hazard="slick roots hiding in shadow",
        need_aid="light",
        fox_lure='The whispering fox said, "Take the bright shortcut alone, and keep the light for yourself."',
        warning_line="Bright things are not always safe things.",
        safe_detail="When the lantern glow was shared between two faces, the dry roots stood out from the slippery ones.",
        ending_image="the warm glow painted two steady shadows while the fox's own path faded into cold bracken",
        tags={"forest", "light", "caution"},
    ),
    "thorn_bend": TrailSpec(
        id="thorn_bend",
        name="Thorn Bend",
        opening="At Thorn Bend, the forest trail narrowed between berry thorns and low ash branches.",
        twinkle_source="silver moths rose above a twinkling path that only showed itself to patient eyes",
        hazard="thorns that punish rushing feet",
        need_aid="patience",
        fox_lure='The whispering fox said, "Clutch every berry for yourself and hurry through before your friend slows you."',
        warning_line="A fast mouth can lead to a scratched heart.",
        safe_detail="Once the berries were shared, no one had to rush, and the moths kept circling the open gap instead of the thorn wall.",
        ending_image="berry juice brightened their smiles while the fox listened to thorns scratching his empty shortcut",
        tags={"forest", "patience", "caution"},
    ),
    "pebble_ford": TrailSpec(
        id="pebble_ford",
        name="Pebble Ford",
        opening="At Pebble Ford, the forest trail dipped to a brook where flat stones waited in a line.",
        twinkle_source="moon flecks flashed on a twinkling path across the water",
        hazard="wobbling stones with dark water between them",
        need_aid="balance",
        fox_lure='The whispering fox said, "Leap first and let the slower feet find their own way."',
        warning_line="A path that divides friends can swallow both pride and balance.",
        safe_detail="Holding the vine loop between two sets of paws turned the crossing into one careful rhythm.",
        ending_image="the brook held their joined reflection while the fox stood on the bank with dry paws and no wisdom",
        tags={"forest", "balance", "caution", "water"},
    ),
}

SHARES = {
    "lantern_jar": ShareSpec(
        id="lantern_jar",
        label="lantern jar",
        phrase="a lantern jar with a warm gold glow",
        size=1,
        aid="light",
        comfort="fear",
        material="glass and soft candlelight",
        share_action="{hero} lowered the lantern jar until {companion} could see the ground too.",
        reveal_action="The light did not make the path shorter, but it made the safe steps honest.",
        lesson="What is shared for safety grows wiser instead of smaller.",
        tags={"light", "sharing", "caution"},
    ),
    "berry_pouch": ShareSpec(
        id="berry_pouch",
        label="berry pouch",
        phrase="a berry pouch tied with grass cord",
        size=1,
        aid="patience",
        comfort="hunger",
        material="soft cloth and sweet berries",
        share_action="{hero} opened the berry pouch and gave half its fruit to {companion} before taking another step.",
        reveal_action="A slower belly made a slower pace, and the slower pace was what let the true gap appear.",
        lesson="Sharing can quiet the hurry that leads small feet into trouble.",
        tags={"patience", "sharing", "caution"},
    ),
    "vine_loop": ShareSpec(
        id="vine_loop",
        label="vine loop",
        phrase="a vine loop woven for two paws",
        size=2,
        aid="balance",
        comfort="unsteady",
        material="green vine and knotted reeds",
        share_action="{hero} placed one end of the vine loop in {companion}'s paws and held the other end without tugging.",
        reveal_action="Two careful bodies became one steady line, and the stones no longer felt far apart.",
        lesson="A strong traveler becomes truly strong when strength is shared.",
        tags={"balance", "sharing", "caution", "water"},
    ),
}

COMPANIONS = {
    "moss_mole": CompanionSpec(
        id="moss_mole",
        label="Moss Mole",
        kind="mole",
        need="fear",
        problem="Moss Mole felt small in dim places and could not tell a dry root from a wet one.",
        thanks='"I can walk when I can see," Moss Mole said softly.',
        pace="slow, careful steps",
        tags={"light", "forest"},
    ),
    "lark_wren": CompanionSpec(
        id="lark_wren",
        label="Lark Wren",
        kind="wren",
        need="hunger",
        problem="Lark Wren had flown a long way and her little chest fluttered with hunger.",
        thanks='"Now I can think before I hurry," Lark Wren chirped.',
        pace="small, thoughtful hops",
        tags={"patience", "forest"},
    ),
    "tansy_turtle": CompanionSpec(
        id="tansy_turtle",
        label="Tansy Turtle",
        kind="turtle",
        need="unsteady",
        problem="Tansy Turtle slipped whenever loose stones rolled under her shell.",
        thanks='"Together feels steadier than alone," Tansy Turtle said.',
        pace="slow, anchored steps",
        tags={"balance", "water", "forest"},
    ),
}

KNOWLEDGE = {
    "sharing": [
        QAItem(
            "Why can sharing make a trail safer?",
            "Sharing can spread out the useful thing instead of trapping it in one pair of paws. In this world, safety comes from making enough light, food, or balance for both travelers."
        ),
        QAItem(
            "Why is selfish advice risky in a fable?",
            "Selfish advice sounds quick and clever, but it usually hides who will be left in danger. A fable uses that trick to show that character matters as much as cleverness."
        ),
    ],
    "light": [
        QAItem(
            "Why does shared light help on a root-covered trail?",
            "Shared light lets both walkers judge where to place their feet. That matters because a safe root and a slick root can look almost the same in the dark."
        ),
    ],
    "patience": [
        QAItem(
            "Why can food change a decision on the trail?",
            "A hungry traveler is more likely to rush and make a poor guess. A little food can slow the body enough for wiser choices to return."
        ),
    ],
    "balance": [
        QAItem(
            "Why does crossing together help at a brook?",
            "Crossing together spreads fear and steadies movement across the slippery stones. When both walkers move in one rhythm, balance becomes easier to keep."
        ),
    ],
    "water": [
        QAItem(
            "Why are shiny stones near water not always trustworthy?",
            "Water can make surfaces look brighter and flatter than they really are. A sparkle may mark a crossing, but it does not promise that every step is safe."
        ),
    ],
}


def combo_is_valid(hero: HeroSpec, trail: TrailSpec, share: ShareSpec, companion: CompanionSpec) -> bool:
    return share.size in hero.carries and share.aid == trail.need_aid and share.comfort == companion.need


def sentence_case(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    return text[0].upper() + text[1:]


def explain_rejection(hero: HeroSpec, trail: TrailSpec, share: ShareSpec, companion: CompanionSpec) -> str:
    if share.size not in hero.carries:
        return (
            f"No story: {hero.label} cannot reasonably carry {share.phrase}. "
            f"{hero.label} handles sizes {sorted(hero.carries)} but {share.label} is size {share.size}."
        )
    if share.aid != trail.need_aid:
        return (
            f"No story: {share.phrase} helps with {share.aid}, but {trail.name} needs {trail.need_aid} "
            f"to make the twinkling path safe."
        )
    if share.comfort != companion.need:
        return (
            f"No story: {companion.label} needs help with {companion.need}, but {share.phrase} comforts {share.comfort}."
        )
    return "No story: the requested combination is unreasonable."


def all_params() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for hero_id, hero in HEROES.items():
        for trail_id, trail in TRAILS.items():
            for share_id, share in SHARES.items():
                for companion_id, companion in COMPANIONS.items():
                    if combo_is_valid(hero, trail, share, companion):
                        combos.append(
                            StoryParams(
                                hero=hero_id,
                                trail=trail_id,
                                share=share_id,
                                companion=companion_id,
                            )
                        )
    return combos


def matching_params(args: argparse.Namespace) -> list[StoryParams]:
    out: list[StoryParams] = []
    for params in all_params():
        if args.hero is not None and params.hero != args.hero:
            continue
        if args.trail is not None and params.trail != args.trail:
            continue
        if args.share is not None and params.share != args.share:
            continue
        if args.companion is not None and params.companion != args.companion:
            continue
        out.append(params)
    return out


def make_world(params: StoryParams) -> StoryWorld:
    hero = HEROES[params.hero]
    trail = TRAILS[params.trail]
    share = SHARES[params.share]
    companion = COMPANIONS[params.companion]
    if not combo_is_valid(hero, trail, share, companion):
        raise StoryError(explain_rejection(hero, trail, share, companion))

    world = StoryWorld(params=params)
    world.facts["hero_spec"] = hero
    world.facts["trail_spec"] = trail
    world.facts["share_spec"] = share
    world.facts["companion_spec"] = companion
    world.facts["solved"] = False
    world.facts["shared"] = False
    world.facts["learned"] = False

    world.add(
        Entity(
            id="hero",
            label=hero.label,
            kind=hero.kind,
            type="hero",
            meters={"distance_home": 3, "load_size": share.size},
            memes={"temptation": 1, "caution": 0, "generosity": 0},
            attrs={"trait": hero.trait},
        )
    )
    world.add(
        Entity(
            id="companion",
            label=companion.label,
            kind=companion.kind,
            type="companion",
            meters={"comfort": 0, "steady": 0},
            memes={"trust": 0},
            attrs={"pace": companion.pace},
        )
    )
    world.add(
        Entity(
            id="fox",
            label="the whispering fox",
            kind="fox",
            type="tempter",
            meters={"distance": 1},
            memes={"mischief": 2, "influence": 1},
        )
    )
    world.add(
        Entity(
            id="share",
            label=share.label,
            kind="object",
            type="shared_item",
            meters={"shared": 0, "in_use": 0},
            memes={"care": 0},
            attrs={"material": share.material},
        )
    )
    world.add(
        Entity(
            id="trail",
            label=trail.name,
            kind="place",
            type="trail",
            meters={"risk": 2, "crossed": 0},
            memes={"welcome": 0},
        )
    )
    return world


def introduce(world: StoryWorld) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    trail: TrailSpec = world.facts["trail_spec"]
    share: ShareSpec = world.facts["share_spec"]
    hero_spec: HeroSpec = world.facts["hero_spec"]
    world.record(
        "beginning",
        "hero",
        "trail",
        f"{trail.opening} {hero.label}, a {hero_spec.trait} {hero.kind}, walked there with {companion.label} on the way to {hero_spec.home}. {hero.label} carried {share.phrase}, and {trail.twinkle_source}.",
        target="companion",
    )
    world.record(
        "premise",
        "companion",
        "trail",
        f"{companion.label} stayed close because {COMPANIONS[world.params.companion].problem} The path looked lovely, but its beauty sat beside {trail.hazard}.",
        target="trail",
    )


def fox_whispers(world: StoryWorld) -> None:
    trail: TrailSpec = world.facts["trail_spec"]
    hero_spec: HeroSpec = world.facts["hero_spec"]
    world.para()
    world.record(
        "temptation",
        "fox",
        "trail",
        f"From the fern shade came the whispering fox. {trail.fox_lure}",
        target="hero",
    )
    world.record(
        "warning",
        "hero",
        "trail",
        f"{hero_spec.caution_voice} {trail.warning_line}",
        target="fox",
    )


def choose_sharing(world: StoryWorld) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    fox = world.get("fox")
    share_ent = world.get("share")
    share: ShareSpec = world.facts["share_spec"]
    companion_spec: CompanionSpec = world.facts["companion_spec"]
    world.para()
    world.record(
        "turn",
        "hero",
        "trail",
        f"{hero.label} looked at {companion.label} instead of the bright shortcut. {share.share_action.format(hero=hero.label, companion=companion.label)}",
        target="share",
    )
    share_ent.meters["shared"] = 1
    share_ent.meters["in_use"] = 1
    share_ent.memes["care"] = 1
    companion.meters["comfort"] = 1
    companion.memes["trust"] = 1
    hero.memes["generosity"] = 1
    hero.memes["caution"] = 1
    hero.memes["temptation"] = 0
    fox.memes["influence"] = 0
    world.facts["shared"] = True
    world.record(
        "comfort",
        "companion",
        "trail",
        f"{companion_spec.thanks} The fox's sweet whisper sounded smaller once the two friends were acting like one little team.",
        target="hero",
    )


def cross_safely(world: StoryWorld) -> None:
    hero = world.get("hero")
    trail_ent = world.get("trail")
    trail: TrailSpec = world.facts["trail_spec"]
    share: ShareSpec = world.facts["share_spec"]
    world.para()
    world.record(
        "resolution",
        "hero",
        "trail",
        f"{trail.safe_detail} {share.reveal_action}",
        target="trail",
    )
    world.record(
        "arrival",
        "hero",
        "trail",
        f"So {hero.label} and {world.get('companion').label} crossed the dangerous place with measured steps and left the whispering fox behind in the brush.",
        target="fox",
    )
    trail_ent.meters["risk"] = 0
    trail_ent.meters["crossed"] = 1
    trail_ent.memes["welcome"] = 1
    hero.meters["distance_home"] = 0
    world.get("companion").meters["steady"] = 1
    world.facts["solved"] = True


def close_fable(world: StoryWorld) -> None:
    trail: TrailSpec = world.facts["trail_spec"]
    share: ShareSpec = world.facts["share_spec"]
    world.para()
    world.record(
        "ending",
        "hero",
        "trail",
        f"At the end of the forest trail, the lesson felt plain: {share.lesson} {sentence_case(trail.ending_image)}.",
        target="trail",
    )
    world.record(
        "moral",
        "hero",
        "trail",
        "The fable's warning was this: never trust a voice that tells you to shine alone when the safe way is to share.",
        target="fox",
    )
    world.facts["learned"] = True


def tell(params: StoryParams) -> StoryWorld:
    world = make_world(params)
    introduce(world)
    fox_whispers(world)
    choose_sharing(world)
    cross_safely(world)
    close_fable(world)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    hero: HeroSpec = world.facts["hero_spec"]
    trail: TrailSpec = world.facts["trail_spec"]
    companion: CompanionSpec = world.facts["companion_spec"]
    share: ShareSpec = world.facts["share_spec"]
    return [
        'Write a fable set on a forest trail that includes the words "twinkling path" and "whispering fox."',
        f"Tell a cautionary sharing story where {hero.label} ignores selfish advice and helps {companion.label}.",
        f"Make the resolution depend on sharing {share.label} so the danger at {trail.name} becomes safely understandable.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    hero: HeroSpec = world.facts["hero_spec"]
    trail: TrailSpec = world.facts["trail_spec"]
    share: ShareSpec = world.facts["share_spec"]
    companion: CompanionSpec = world.facts["companion_spec"]
    return [
        QAItem(
            "Who was tempted by the whispering fox?",
            f"{hero.label} was the one the fox tried to tempt. The fox wanted {hero.label} to rush ahead and stop thinking about what {companion.label} needed."
        ),
        QAItem(
            "Why was the twinkling path not safe at first?",
            f"It glittered beautifully, but beauty did not remove the danger of {trail.hazard}. The path only became safe when the travelers used the right kind of shared help instead of trusting sparkle alone."
        ),
        QAItem(
            "What did the hero share, and why did that matter?",
            f"{hero.label} shared {share.phrase}. That mattered because the same object comforted {companion.label} and solved the trail's real problem at the same time."
        ),
        QAItem(
            "How did the story turn away from the fox's advice?",
            f"The turn came when {hero.label} looked at {companion.label} instead of the shortcut. That choice broke the fox's influence because care replaced hurry."
        ),
        QAItem(
            "What changed by the ending image?",
            f"By the end, the two friends were moving safely together and the whispering fox had been left behind. The final image proves that shared caution carried them farther than selfish cleverness would have."
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    trail: TrailSpec = world.facts["trail_spec"]
    share: ShareSpec = world.facts["share_spec"]
    companion: CompanionSpec = world.facts["companion_spec"]
    tags = {"sharing"} | set(trail.tags) | set(share.tags) | set(companion.tags)
    ordered = ["sharing", "light", "patience", "balance", "water"]
    out: list[QAItem] = []
    for tag in ordered:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out[:4]


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for event in world.history:
        target = f" -> {event.target}" if event.target else ""
        lines.append(f"{event.id:10} {event.actor}{target} @ {event.place}: {event.text}")
    lines.append("--- entity state ---")
    for entity in world.entities.values():
        bits = []
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        if entity.attrs:
            bits.append(f"attrs={entity.attrs}")
        lines.append(f"{entity.id:10} ({entity.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(H,S) :- hero_carries(H,Size), share_size(S,Size).
helps(S,C) :- share_comfort(S,Need), companion_need(C,Need).
guides(S,T) :- share_aid(S,Aid), trail_need(T,Aid).
valid(H,T,S,C) :- hero(H), trail(T), share(S), companion(C), fits(H,S), helps(S,C), guides(S,T).
ok :- chosen(H,T,S,C), valid(H,T,S,C).

#show valid/4.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds import asp

    rows: list[str] = []
    for hero_id, hero in HEROES.items():
        rows.append(asp.fact("hero", hero_id))
        for size in sorted(hero.carries):
            rows.append(asp.fact("hero_carries", hero_id, size))
    for trail_id, trail in TRAILS.items():
        rows.append(asp.fact("trail", trail_id))
        rows.append(asp.fact("trail_need", trail_id, trail.need_aid))
    for share_id, share in SHARES.items():
        rows.append(asp.fact("share", share_id))
        rows.append(asp.fact("share_size", share_id, share.size))
        rows.append(asp.fact("share_aid", share_id, share.aid))
        rows.append(asp.fact("share_comfort", share_id, share.comfort))
    for companion_id, companion in COMPANIONS.items():
        rows.append(asp.fact("companion", companion_id))
        rows.append(asp.fact("companion_need", companion_id, companion.need))
    if params is not None:
        rows.append(asp.fact("chosen", params.hero, params.trail, params.share, params.companion))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world missing")
    story_lower = sample.story.lower()
    if "twinkling path" not in story_lower:
        raise AssertionError("story is missing 'twinkling path'")
    if "whispering fox" not in story_lower:
        raise AssertionError("story is missing 'whispering fox'")
    if "forest trail" not in story_lower:
        raise AssertionError("story is missing 'forest trail'")
    if sample.story.count("\n\n") < 4:
        raise AssertionError("story should have at least five paragraphs")
    if not world.facts.get("shared"):
        raise AssertionError("story never entered a shared state")
    if not world.facts.get("solved") or not world.facts.get("learned"):
        raise AssertionError("story did not resolve into a learned cautionary ending")
    if world.get("share").meters.get("shared", 0) < 1:
        raise AssertionError("shared object was never shared")
    if world.get("companion").meters.get("comfort", 0) < 1:
        raise AssertionError("companion was never helped")
    if world.get("trail").meters.get("crossed", 0) < 1:
        raise AssertionError("trail was never safely crossed")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 5 or len(sample.world_qa) < 2:
        raise AssertionError("QA sets are too thin")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked formatting markers")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 10:
            raise AssertionError(f"answer too short for question: {item.question}")
        if "." not in item.answer:
            raise AssertionError(f"answer should be full-sentence prose: {item.question}")


def verify() -> int:
    py = sorted((p.hero, p.trail, p.share, p.companion) for p in all_params())
    asp = sorted(asp_valid_combos())
    if py != asp:
        print("MISMATCH between Python and ASP gates:")
        only_py = sorted(set(py) - set(asp))
        only_asp = sorted(set(asp) - set(py))
        if only_py:
            print("  only in Python:", only_py)
        if only_asp:
            print("  only in ASP:", only_asp)
        return 1
    print(f"OK: ASP parity matches Python gate ({len(py)} valid combinations).")
    for params in all_params():
        verify_sample(generate(params))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a small forest-trail fable about a twinkling path, a whispering fox, caution, and sharing."
    )
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--trail", choices=sorted(TRAILS))
    parser.add_argument("--share", choices=sorted(SHARES))
    parser.add_argument("--companion", choices=sorted(COMPANIONS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = matching_params(args)
    if not combos:
        if all(getattr(args, name) is not None for name in ("hero", "trail", "share", "companion")):
            hero = HEROES[args.hero]
            trail = TRAILS[args.trail]
            share = SHARES[args.share]
            companion = COMPANIONS[args.companion]
            raise StoryError(explain_rejection(hero, trail, share, companion))
        raise StoryError("(No valid forest-trail fable matches the given options.)")
    choice = rng.choice(combos)
    return StoryParams(
        hero=choice.hero,
        trail=choice.trail,
        share=choice.share,
        companion=choice.companion,
        seed=args.seed + index,
    )


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Story prompts =="]
    lines.extend(f"{idx}. {prompt}" for idx, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story-grounded QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
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


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(" ".join(combo))
        return 0

    try:
        if args.all:
            samples = [
                generate(
                    StoryParams(
                        hero=params.hero,
                        trail=params.trail,
                        share=params.share,
                        companion=params.companion,
                        seed=args.seed + idx,
                    )
                )
                for idx, params in enumerate(matching_params(args))
            ]
            if not samples:
                raise StoryError("(No valid forest-trail fable matches the given options.)")
        else:
            samples = []
            pool = matching_params(args)
            if not pool:
                raise StoryError("(No valid forest-trail fable matches the given options.)")
            target = max(1, args.n)
            cycles = (target + len(pool) - 1) // len(pool)
            ordered: list[StoryParams] = []
            for cycle in range(cycles):
                rng = random.Random(args.seed + cycle)
                block = list(pool)
                rng.shuffle(block)
                ordered.extend(block)
            for idx, params in enumerate(ordered[:target]):
                samples.append(
                    generate(
                        StoryParams(
                            hero=params.hero,
                            trail=params.trail,
                            share=params.share,
                            companion=params.companion,
                            seed=args.seed + idx,
                        )
                    )
                )
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for idx, sample in enumerate(samples, 1):
        header = f"### variant {idx}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print("\n" + "=" * 72 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
