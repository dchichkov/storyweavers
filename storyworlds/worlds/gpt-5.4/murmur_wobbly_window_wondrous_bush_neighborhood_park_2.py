#!/usr/bin/env python3
"""
Tall-tale storyworld for:
  Words: murmur, wobbly window, wondrous bush
  Setting: neighborhood park
  Features: Magic, Kindness

Internal source tale:
    In a neighborhood park, a loose old window on a small park building catches
    the murmur of a wondrous bush in trouble and throws that whisper across the
    path like a trumpet. Two children could treat the sound as a joke, but they
    choose kindness instead. Once they find the bush's real problem and help it
    with patient hands, the bush answers with outsized magic that changes the
    whole park's evening light.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass(frozen=True)
class Park:
    id: str
    place: str
    opening: str
    closing_view: str
    supports: frozenset[str]


@dataclass(frozen=True)
class Window:
    id: str
    phrase: str
    location: str
    rattle_line: str
    relay_needs: frozenset[str]
    flash_line: str


@dataclass(frozen=True)
class Bush:
    id: str
    phrase: str
    location: str
    need: str
    murmur_words: str
    need_line: str
    magic_name: str
    magic_line: str
    final_image: str
    lesson_line: str
    tags: frozenset[str]


@dataclass(frozen=True)
class KindAct:
    id: str
    label: str
    solves: frozenset[str]
    tool: str
    action_line: str
    care_line: str
    proof_line: str
    tags: frozenset[str]


class World:
    def __init__(self, park: Park) -> None:
        self.park = park
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[dict[str, str]] = []
        self.fired: set[tuple[str, ...]] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, ent_id: str) -> Entity:
        return self.entities[ent_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def note(self, event: str, **fields: str) -> None:
        item = {"event": event}
        item.update(fields)
        self.history.append(item)

    def render(self) -> str:
        return "\n\n".join(" ".join(chunk) for chunk in self.paragraphs if chunk)


def role(world: World, name: str) -> Optional[Entity]:
    return next((ent for ent in world.entities.values() if ent.role == name), None)


PARKS = {
    "cedar_whirl": Park(
        id="cedar_whirl",
        place="Cedar Whirl Park",
        opening="the slide gleamed so hard it looked ready to butter the clouds, and the swings pumped the air like silver porch bells",
        closing_view="The fountain bowl held the sunset as neatly as soup in a blue china cup",
        supports=frozenset({"tool_shed", "gazebo", "rose_walk", "kite_fence"}),
    ),
    "penny_meadow": Park(
        id="penny_meadow",
        place="Penny Meadow Park",
        opening="the hopscotch stones sat in a row like giant coins and the benches looked polished enough for mayors or moonbeams",
        closing_view="The path lamps blinked on one by one like careful fireflies learning manners",
        supports=frozenset({"tool_shed", "snack_kiosk", "rose_walk", "story_circle"}),
    ),
    "sunbeam_green": Park(
        id="sunbeam_green",
        place="Sunbeam Green Park",
        opening="the bandstand roof held one corner of the afternoon up while the monkey bars stretched themselves as if they meant to shake hands with the stars",
        closing_view="The puddle by the curb went bright enough to look like a pocket mirror for the whole sky",
        supports=frozenset({"snack_kiosk", "gazebo", "kite_fence", "story_circle"}),
    ),
}

WINDOWS = {
    "shed_window": Window(
        id="shed_window",
        phrase="the wobbly window on the tool shed",
        location="tool_shed",
        rattle_line="chattered like a tin spoon in a teacup",
        relay_needs=frozenset({"thirst", "lean"}),
        flash_line="A skinny stripe of light jumped from the pane and skipped across the dirt path.",
    ),
    "kiosk_window": Window(
        id="kiosk_window",
        phrase="the wobbly window on the snack kiosk",
        location="snack_kiosk",
        rattle_line="clicked and hummed like two marbles trying to sing a duet",
        relay_needs=frozenset({"thirst", "snag"}),
        flash_line="Its loose corner winked so brightly that even the napkin box looked startled.",
    ),
    "gazebo_window": Window(
        id="gazebo_window",
        phrase="the wobbly window on the little gazebo cabinet",
        location="gazebo",
        rattle_line="rumbled in its frame like a brave drum with only one stick",
        relay_needs=frozenset({"snag", "lean"}),
        flash_line="Its glass shivered with a pale shine that turned the railing silver for a heartbeat.",
    ),
}

BUSHES = {
    "thunderberry": Bush(
        id="thunderberry",
        phrase="a wondrous bush heavy with copper-blue berries",
        location="rose_walk",
        need="thirst",
        murmur_words="A sip for my roots, if you please",
        need_line="The dirt at its feet had cracked into dry little scales, and the leaves had begun to curl at the edges.",
        magic_name="rain_berries",
        magic_line="The berries swelled with clear light and tinkled until the whole branch sounded like a tiny rainstorm wearing glass shoes.",
        final_image="Above the rose walk, bright drops hung from every berry and made a ceiling of sparkling weather.",
        lesson_line="The children had listened to a small thirsty problem before it could grow into a grand unhappy one.",
        tags=frozenset({"bush", "water", "berries", "magic"}),
    ),
    "streamerramble": Bush(
        id="streamerramble",
        phrase="a wondrous bush braided with ribbon-bright leaves",
        location="kite_fence",
        need="snag",
        murmur_words="Please loose my sleeves from this tangle",
        need_line="A torn kite tail had wrapped around the top branches until the leaves could only flutter in short, fussy jerks.",
        magic_name="lantern_streamers",
        magic_line="The freed leaves whirled up in a ring and glowed like parade streamers that had borrowed their light from Saturday night.",
        final_image="Over the fence, shining ribbons floated in the dusk as neatly as laundry hung by giants.",
        lesson_line="Their gentle patience loosened a knot that rough hands would only have pulled tighter.",
        tags=frozenset({"bush", "ribbons", "kite", "magic"}),
    ),
    "moonmyrtle": Bush(
        id="moonmyrtle",
        phrase="a wondrous bush with round silver leaves",
        location="story_circle",
        need="lean",
        murmur_words="Please hold up my tired arm",
        need_line="One broad branch had slumped low over the storytelling stump and shook every time the breeze tested it.",
        magic_name="silver_blossoms",
        magic_line="Where the branch stood steady again, pale blossoms popped open all at once and lit the air like pocket moons.",
        final_image="Around the story circle, the leaves glowed so softly that the stump looked ready to tell bedtime to the whole block.",
        lesson_line="A kindly brace can steady both a branch and the brave heart that bends to help it.",
        tags=frozenset({"bush", "branch", "blossoms", "magic"}),
    ),
}

ACTS = {
    "share_water": KindAct(
        id="share_water",
        label="share water with the roots",
        solves=frozenset({"thirst"}),
        tool="a red pail from the fountain",
        action_line="The children carried the pail together and tipped the water slowly, letting the thirsty ground drink without washing the roots bare.",
        care_line="They poured as carefully as if they were helping a sleepy baby wake up without a fuss.",
        proof_line="The hard dirt darkened, and the murmur melted into a relieved little hum.",
        tags=frozenset({"kindness", "water"}),
    ),
    "free_streamers": KindAct(
        id="free_streamers",
        label="free the tangled branches",
        solves=frozenset({"snag"}),
        tool="patient fingers and a low park stool",
        action_line="They climbed the stool one at a time and eased each loop free, never yanking, never snapping, and never hurrying the knot.",
        care_line="They treated every leaf and ribbon as if it belonged on a parade costume that must not tear.",
        proof_line="The trapped branches sprang loose with a soft sigh, and the murmur turned bright as a thank-you whistle.",
        tags=frozenset({"kindness", "patience"}),
    ),
    "prop_branch": KindAct(
        id="prop_branch",
        label="prop the drooping branch",
        solves=frozenset({"lean"}),
        tool="a smooth stick and a sweater tied into a soft sling",
        action_line="They set the stick beneath the branch and wrapped the sweater around it so the bark would rest on cloth instead of rubbing raw.",
        care_line="They watched the branch and the ground below at the same time, making sure help felt gentle from top to bottom.",
        proof_line="The shaking stopped at once, and the murmur settled into the calm sound of someone finally catching a full breath.",
        tags=frozenset({"kindness", "care"}),
    ),
}

GIRL_NAMES = ["Mina", "Lula", "Nia", "Poppy", "Tess", "Wren"]
BOY_NAMES = ["Arlo", "Bram", "Eli", "Milo", "Ned", "Theo"]
TRAITS = ["kind", "curious", "steady", "bright-eyed", "careful"]


@dataclass
class StoryParams:
    park: str
    window: str
    bush: str
    act: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


def park_supports(park: Park, location: str) -> bool:
    return location in park.supports


def window_relays(window: Window, bush: Bush) -> bool:
    return bush.need in window.relay_needs


def act_solves(act: KindAct, bush: Bush) -> bool:
    return bush.need in act.solves


def valid_combo(park: Park, window: Window, bush: Bush, act: KindAct) -> bool:
    return (
        park_supports(park, window.location)
        and park_supports(park, bush.location)
        and window_relays(window, bush)
        and act_solves(act, bush)
    )


def explain_rejection(park: Park, window: Window, bush: Bush, act: KindAct) -> str:
    if not park_supports(park, window.location):
        return f"(No story: {park.place} has no good place for {window.phrase}.)"
    if not park_supports(park, bush.location):
        return f"(No story: {park.place} cannot host {bush.phrase} in this setup.)"
    if not window_relays(window, bush):
        return f"(No story: {window.phrase} would not carry a murmur about {bush.need} trouble.)"
    return f"(No story: the plan to {act.label} does not fix the bush's real need.)"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for park_id, park in PARKS.items():
        for window_id, window in WINDOWS.items():
            for bush_id, bush in BUSHES.items():
                for act_id, act in ACTS.items():
                    if valid_combo(park, window, bush, act):
                        combos.append((park_id, window_id, bush_id, act_id))
    return sorted(combos)


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.park and args.window and args.bush and args.act:
        park = PARKS[args.park]
        window = WINDOWS[args.window]
        bush = BUSHES[args.bush]
        act = ACTS[args.act]
        if not valid_combo(park, window, bush, act):
            raise StoryError(explain_rejection(park, window, bush, act))

    combos = [
        combo
        for combo in valid_combos()
        if (args.park is None or combo[0] == args.park)
        and (args.window is None or combo[1] == args.window)
        and (args.bush is None or combo[2] == args.bush)
        and (args.act is None or combo[3] == args.act)
    ]
    if not combos:
        raise StoryError("(No valid neighborhood-park tall tale matches the given options.)")

    park_id, window_id, bush_id, act_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    return StoryParams(
        park=park_id,
        window=window_id,
        bush=bush_id,
        act=act_id,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        trait=rng.choice(TRAITS),
    )


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_r_window_relays, _r_children_choose_kindness, _r_repair_bush, _r_bush_returns_magic):
            before = len(world.fired)
            rule(world)
            if len(world.fired) > before:
                changed = True


def _r_window_relays(world: World) -> None:
    park_ent = world.get("park")
    window_ent = world.get("window")
    bush_ent = world.get("bush")
    if window_ent.meters["wobbling"] < THRESHOLD or bush_ent.meters["troubled"] < THRESHOLD:
        return
    sig = ("window_relays",)
    if sig in world.fired:
        return
    world.fired.add(sig)
    window_ent.meters["carrying_murmur"] += 1
    bush_ent.meters["heard"] += 1
    park_ent.meters["hushed"] += 1
    hero = role(world, "hero")
    friend = role(world, "friend")
    if hero is not None:
        hero.memes["wonder"] += 1
    if friend is not None:
        friend.memes["wonder"] += 1
    world.note("window_relays_murmur", source="window", target="children")


def _r_children_choose_kindness(world: World) -> None:
    hero = role(world, "hero")
    friend = role(world, "friend")
    window_ent = world.get("window")
    bush_ent = world.get("bush")
    if hero is None or friend is None:
        return
    if window_ent.meters["carrying_murmur"] < THRESHOLD:
        return
    sig = ("children_choose_kindness",)
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    hero.memes["concern"] += 1
    friend.memes["concern"] += 1
    bush_ent.memes["hope"] += 1
    world.note("children_choose_kindness", choice="help", reason="heard_real_need")


def _r_repair_bush(world: World) -> None:
    hero = role(world, "hero")
    friend = role(world, "friend")
    bush_ent = world.get("bush")
    act_ent = world.get("act")
    if hero is None or friend is None:
        return
    if hero.memes["kindness"] < THRESHOLD or friend.memes["kindness"] < THRESHOLD:
        return
    if act_ent.meters["attempted"] < THRESHOLD:
        return
    sig = ("repair_bush",)
    if sig in world.fired:
        return
    world.fired.add(sig)
    bush_ent.meters["troubled"] = 0.0
    bush_ent.meters["restored"] += 1
    act_ent.meters["worked"] += 1
    bush_ent.memes["relief"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.note(
        "bush_repaired",
        act=world.facts["act_cfg"].id,
        need=world.facts["bush_cfg"].need,
    )


def _r_bush_returns_magic(world: World) -> None:
    park_ent = world.get("park")
    window_ent = world.get("window")
    bush_ent = world.get("bush")
    if bush_ent.meters["restored"] < THRESHOLD:
        return
    sig = ("bush_returns_magic",)
    if sig in world.fired:
        return
    world.fired.add(sig)
    bush_ent.meters["glowing"] += 1
    window_ent.meters["gleaming"] += 1
    park_ent.meters["sparkling"] += 1
    bush_ent.memes["magic"] += 1
    world.note(
        "bush_returns_magic",
        magic=world.facts["bush_cfg"].magic_name,
        witness="window",
    )


def introduce(world: World, hero: Entity, friend: Entity, window_cfg: Window, bush_cfg: Bush) -> None:
    world.say(
        f"In {world.park.place}, a neighborhood park where {world.park.opening}, "
        f"{hero.id}, a {hero.traits[0]} child, wandered beside {friend.id} after supper."
    )
    world.say(
        f"Near the path stood {window_cfg.phrase}, and beyond it waited {bush_cfg.phrase}."
    )
    world.say(
        "Folks said that park could stretch a whisper until it fit clear across the block, and that evening it meant to prove it."
    )


def wake_window(world: World, window_ent: Entity, window_cfg: Window) -> None:
    park_ent = world.get("park")
    window_ent.meters["wobbling"] += 1
    park_ent.meters["windy"] += 1
    world.note("window_wobbles", sound=window_cfg.rattle_line)
    propagate(world)
    world.say(
        f"A puff of wind found the loose frame, and {window_cfg.phrase} {window_cfg.rattle_line}."
    )
    world.say(window_cfg.flash_line)


def hear_murmur(world: World, hero: Entity, friend: Entity, bush_cfg: Bush) -> None:
    bush_ent = world.get("bush")
    if bush_ent.meters["heard"] < THRESHOLD:
        return
    world.say(
        f"Out of the racket came a murmur so plain that {hero.id} grabbed {friend.id}'s sleeve. "
        f'"{bush_cfg.murmur_words}," it seemed to say.'
    )
    world.say(
        f"{friend.id} peered past the wobbling glass and spotted the wondrous bush moving as if it were raising a leafy hand."
    )
    world.say(
        "The two children could have laughed and run, but kindness tugged them closer instead of farther."
    )


def inspect_trouble(world: World, hero: Entity, friend: Entity, bush_cfg: Bush, act_cfg: KindAct) -> None:
    world.note("trouble_seen", need=bush_cfg.need, location=bush_cfg.location)
    world.say(
        f"They hurried over and found the truth under the tall-tale noise. {bush_cfg.need_line}"
    )
    world.say(
        f'"If something in the park asks that politely, we ought to answer politely," said {hero.id}.'
    )
    world.say(
        f"So {hero.id} and {friend.id} chose to {act_cfg.label} using {act_cfg.tool}."
    )


def do_kindness(world: World, hero: Entity, friend: Entity, act_ent: Entity, act_cfg: KindAct) -> None:
    act_ent.meters["attempted"] += 1
    world.note("kindness_attempted", act=act_cfg.id)
    propagate(world)
    world.say(act_cfg.action_line)
    world.say(act_cfg.care_line)
    world.say(
        f"{hero.id} took the first turn, then {friend.id} took the second, so the work stayed fair and the help stayed gentle."
    )


def reveal_magic(world: World, bush_cfg: Bush, act_cfg: KindAct) -> None:
    bush_ent = world.get("bush")
    window_ent = world.get("window")
    if bush_ent.meters["restored"] < THRESHOLD:
        return
    world.say(act_cfg.proof_line)
    if bush_ent.memes["magic"] >= THRESHOLD:
        world.say(bush_cfg.magic_line)
    if window_ent.meters["gleaming"] >= THRESHOLD:
        world.say(
            "The shine bounced back into the wobbly window until the old pane looked smooth enough to hold a whole extra sunset."
        )


def close_story(world: World, hero: Entity, friend: Entity, bush_cfg: Bush) -> None:
    world.say(f"{bush_cfg.final_image} {world.park.closing_view}.")
    world.say(
        f"{hero.id} and {friend.id} walked home knowing a small kind deed can begin as a murmur and end as a legend."
    )
    world.say(bush_cfg.lesson_line)
    world.facts["resolved"] = world.get("bush").meters["restored"] >= THRESHOLD


def tell(
    park: Park,
    window_cfg: Window,
    bush_cfg: Bush,
    act_cfg: KindAct,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    trait: str,
) -> World:
    world = World(park)
    park_ent = world.add(Entity("park", "place", "park", park.place, tags={"park", "neighborhood"}))
    hero = world.add(Entity(hero_name, "character", hero_gender, hero_name, role="hero", traits=[trait]))
    friend = world.add(Entity(friend_name, "character", friend_gender, friend_name, role="friend"))
    window_ent = world.add(Entity("window", "thing", "window", "wobbly window", tags={"window", "sound"}))
    bush_ent = world.add(Entity("bush", "plant", "bush", "wondrous bush", tags=set(bush_cfg.tags)))
    act_ent = world.add(Entity("act", "plan", "kind_act", act_cfg.label, tags=set(act_cfg.tags)))

    bush_ent.meters["troubled"] = 1
    park_ent.meters["open"] = 1

    world.facts.update(
        park=park,
        park_ent=park_ent,
        window_cfg=window_cfg,
        bush_cfg=bush_cfg,
        act_cfg=act_cfg,
        hero=hero,
        friend=friend,
    )

    introduce(world, hero, friend, window_cfg, bush_cfg)
    wake_window(world, window_ent, window_cfg)

    world.para()
    hear_murmur(world, hero, friend, bush_cfg)
    inspect_trouble(world, hero, friend, bush_cfg, act_cfg)

    world.para()
    do_kindness(world, hero, friend, act_ent, act_cfg)
    reveal_magic(world, bush_cfg, act_cfg)
    close_story(world, hero, friend, bush_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    bush_cfg: Bush = world.facts["bush_cfg"]  # type: ignore[assignment]
    act_cfg: KindAct = world.facts["act_cfg"]  # type: ignore[assignment]
    return [
        'Write a Tall Tale for young children set in a neighborhood park that includes the words "murmur," "wobbly window," and "wondrous bush."',
        f"Tell a magical kindness story where {hero.id} and {friend.id} hear a murmur through a wobbly window and discover that {bush_cfg.phrase} needs help.",
        f"Write a child-friendly tall tale where the children choose to {act_cfg.label} and the park ends with a big, visible magical image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    park: Park = world.facts["park"]  # type: ignore[assignment]
    window_cfg: Window = world.facts["window_cfg"]  # type: ignore[assignment]
    bush_cfg: Bush = world.facts["bush_cfg"]  # type: ignore[assignment]
    act_cfg: KindAct = world.facts["act_cfg"]  # type: ignore[assignment]
    return [
        (
            "What made the children stop in the park?",
            f"They stopped because {window_cfg.phrase} carried a murmur loudly enough for them to hear it. The rattling pane turned the bush's tiny plea into something impossible to ignore.",
        ),
        (
            "What trouble was the wondrous bush in?",
            f"The wondrous bush needed help because {bush_cfg.need_line.rstrip('.').lower()}. That physical problem was the real source of the strange voice.",
        ),
        (
            "How did the children answer the murmur?",
            f"{hero.id} and {friend.id} answered it by choosing to {act_cfg.label}. They used {act_cfg.tool} because kindness meant fixing the problem carefully, not just quickly.",
        ),
        (
            "Why is the wobbly window important in this story?",
            f"The wobbly window matters because it relayed the bush's trouble across {park.place}. Without that shaky glass, the children might have walked past the need without noticing it.",
        ),
        (
            "What changed after the children helped?",
            f"After the help worked, {bush_cfg.magic_line[0].lower() + bush_cfg.magic_line[1:]} The magic gave the park a new ending image, so everyone could see the change instead of only hearing about it.",
        ),
    ]


KNOWLEDGE = {
    "window": [
        (
            "Why can a loose window make a sound seem bigger?",
            "A loose window can rattle and echo at the same time. That can push a small sound farther and make it easier to notice.",
        )
    ],
    "kindness": [
        (
            "Why is kindness useful when something strange happens?",
            "Kindness keeps people from rushing into mean guesses. It helps them slow down, look closely, and notice the real problem.",
        )
    ],
    "magic": [
        (
            "What makes story magic feel earned?",
            "Story magic feels earned when it grows from what the characters truly did. A kind action can lead to a marvelous result that shows the change in a clear way.",
        )
    ],
    "water": [
        (
            "Why do dry roots need a careful drink?",
            "Roots need water to move food through the plant and keep leaves firm. A careful drink helps the soil soak up water without washing the roots loose.",
        )
    ],
    "patience": [
        (
            "Why does patience help with tangles?",
            "Tangles usually tighten when someone yanks at them. Patient hands can find the first loop and loosen the rest safely.",
        )
    ],
    "care": [
        (
            "Why should a weak branch be propped softly?",
            "A soft support holds the branch up without scraping the bark. That protects the living outer layer while the branch steadies itself.",
        )
    ],
    "berries": [
        (
            "Why do stories often use berries or blossoms in magic scenes?",
            "Berries and blossoms change shape and color in ways children can picture right away. That makes the magic feel visible instead of hidden.",
        )
    ],
    "kite": [
        (
            "Why should people free something caught in a plant gently?",
            "Plants bend and tear more easily than they look. Gentle hands solve the snag without creating a second problem.",
        )
    ],
    "branch": [
        (
            "Why is it smart to support a leaning branch early?",
            "A leaning branch can scrape, split, or fall farther if nobody notices it. Early help keeps the damage small and easier to fix.",
        )
    ],
}

KNOWLEDGE_ORDER = ["window", "kindness", "magic", "water", "patience", "care", "berries", "kite", "branch"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    bush_cfg: Bush = world.facts["bush_cfg"]  # type: ignore[assignment]
    act_cfg: KindAct = world.facts["act_cfg"]  # type: ignore[assignment]
    tags = {"window", "kindness", "magic"} | set(bush_cfg.tags) | set(act_cfg.tags)
    items: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            items.extend(KNOWLEDGE[key])
    return items


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{idx}. {prompt}" for idx, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story world ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts = [f"{ent.id:8} ({ent.type:10})"]
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.traits:
            parts.append(f"traits={ent.traits}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append("  " + " ".join(parts))
    lines.append(f"  fired rules: {sorted(name for name, *_ in world.fired)}")
    lines.append("  history:")
    for item in world.history:
        bits = ", ".join(f"{k}={v}" for k, v in item.items())
        lines.append(f"    - {bits}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cedar_whirl", "shed_window", "thunderberry", "share_water", "Mina", "girl", "Theo", "boy", "kind"),
    StoryParams("cedar_whirl", "gazebo_window", "streamerramble", "free_streamers", "Arlo", "boy", "Nia", "girl", "careful"),
    StoryParams("penny_meadow", "shed_window", "moonmyrtle", "prop_branch", "Poppy", "girl", "Milo", "boy", "steady"),
    StoryParams("sunbeam_green", "kiosk_window", "streamerramble", "free_streamers", "Wren", "girl", "Eli", "boy", "bright-eyed"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PARKS[params.park],
        WINDOWS[params.window],
        BUSHES[params.bush],
        ACTS[params.act],
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
host(P,L)            :- supports(P,L).
window_works(W,B)    :- relay_need(W,N), bush_need(B,N).
act_works(A,B)       :- solves_need(A,N), bush_need(B,N).
valid(P,W,B,A)       :- park(P), window(W), bush(B), act(A),
                        window_loc(W,WL), bush_loc(B,BL),
                        host(P,WL), host(P,BL),
                        window_works(W,B),
                        act_works(A,B).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for park_id, park in PARKS.items():
        lines.append(asp.fact("park", park_id))
        for location in sorted(park.supports):
            lines.append(asp.fact("supports", park_id, location))
    for window_id, window in WINDOWS.items():
        lines.append(asp.fact("window", window_id))
        lines.append(asp.fact("window_loc", window_id, window.location))
        for need in sorted(window.relay_needs):
            lines.append(asp.fact("relay_need", window_id, need))
    for bush_id, bush in BUSHES.items():
        lines.append(asp.fact("bush", bush_id))
        lines.append(asp.fact("bush_loc", bush_id, bush.location))
        lines.append(asp.fact("bush_need", bush_id, bush.need))
    for act_id, act in ACTS.items():
        lines.append(asp.fact("act", act_id))
        for need in sorted(act.solves):
            lines.append(asp.fact("solves_need", act_id, need))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _verify_story_sample(sample: StorySample) -> list[str]:
    issues: list[str] = []
    story = sample.story.lower()
    if "murmur" not in story:
        issues.append("story is missing 'murmur'")
    if "wobbly window" not in story:
        issues.append("story is missing 'wobbly window'")
    if "wondrous bush" not in story:
        issues.append("story is missing 'wondrous bush'")
    if "neighborhood park" not in story:
        issues.append("story is missing neighborhood-park grounding")
    if sample.story.count("\n\n") < 2:
        issues.append("story should have at least three paragraphs")
    if not sample.prompts or not sample.story_qa or not sample.world_qa:
        issues.append("prompt or QA sections are incomplete")
    world = sample.world
    if world is None:
        issues.append("sample is missing world trace")
        return issues
    bush_ent = world.get("bush")
    if bush_ent.meters["restored"] < THRESHOLD:
        issues.append("bush was not restored")
    if bush_ent.memes["magic"] < THRESHOLD:
        issues.append("magic resolution did not fire")
    if role(world, "hero") is None or role(world, "friend") is None:
        issues.append("missing child roles in world state")
    if not world.facts.get("resolved"):
        issues.append("world did not mark itself resolved")
    if len(world.history) < 5:
        issues.append("world history is too thin for grounded QA")
    return issues


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    status = 0
    if python_set != clingo_set:
        print("MISMATCH between Python gate and ASP gate:")
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        status = 1
    else:
        print(f"OK: ASP gate matches Python gate ({len(python_set)} combos).")

    exercise = CURATED + [
        StoryParams(park, window, bush, act, "Mina", "girl", "Theo", "boy", "kind")
        for park, window, bush, act in valid_combos()[:4]
    ]
    for params in exercise:
        sample = generate(params)
        problems = _verify_story_sample(sample)
        if problems:
            print(f"VERIFY FAILED for {(params.park, params.window, params.bush, params.act)}:")
            for item in problems:
                print(f"  - {item}")
            status = 1
    if status == 0:
        print(f"OK: exercised {len(exercise)} generated stories.")
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Story world: murmur, wobbly window, wondrous bush, neighborhood park."
    )
    parser.add_argument("--park", choices=sorted(PARKS))
    parser.add_argument("--window", choices=sorted(WINDOWS))
    parser.add_argument("--bush", choices=sorted(BUSHES))
    parser.add_argument("--act", choices=sorted(ACTS))
    parser.add_argument("--hero")
    parser.add_argument("--hero-gender", choices=["girl", "boy"])
    parser.add_argument("--friend")
    parser.add_argument("--friend-gender", choices=["girl", "boy"])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)

    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (park, window, bush, act) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:18}" for part in combo))
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 60):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return 1
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
        if len(samples) < args.n:
            print(f"(Only found {len(samples)} unique stories for the requested constraints.)")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for idx, sample in enumerate(samples):
        params = sample.params
        header = ""
        if args.all:
            header = f"### {params.hero} & {params.friend}: {params.window}, {params.bush}, {params.act}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
