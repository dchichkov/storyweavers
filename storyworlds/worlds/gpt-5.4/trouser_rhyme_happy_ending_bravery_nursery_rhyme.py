#!/usr/bin/env python3
"""
trouser_rhyme_happy_ending_bravery_nursery_rhyme.py
===================================================

A small StoryWorld for the seed:

    words: trouser
    features: Rhyme, Happy Ending, Bravery
    style: Nursery Rhyme

Internal source tale:
    A child in patchwork trousers hears a tiny creature in trouble near a small
    country lane. The trouble is not huge, but it looks huge to the child at
    first because there is splash, shadow, or a snagging hedge. The child feels
    fear, reaches into the right trouser pocket for a simple helpful thing, and
    uses a brave little rhyme to turn worry into action. The world state then
    determines whether the child can reach, soothe, light, or steady the rescue.
    The ending always lands on a concrete nursery-rhyme image that proves the
    place and the creature are safe again.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Lane:
    key: str
    phrase: str
    landmark: str
    light: int
    footing: int
    reach_anchor: int
    dry_bank: int
    ending_view: str


@dataclass(frozen=True)
class Trouble:
    key: str
    creature_type: str
    creature_phrase: str
    scene_text: str
    fear_cause: str
    obstacle: str
    safe_place: str
    resolve_text: str
    ending_image: str
    lesson: str
    fear_need: int
    light_need: int
    reach_need: int
    steady_need: int
    burr_need: int
    splash_need: int


@dataclass(frozen=True)
class Method:
    key: str
    phrase: str
    pocket_item: str
    brave_rhyme: str
    action_text: str
    calm_boost: int
    light_boost: int
    reach_boost: int
    steady_boost: int
    burr_help: int


@dataclass
class StoryParams:
    lane: str
    trouble: str
    method: str
    hero: str
    gender: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = round(value, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


@dataclass
class World:
    params: StoryParams
    lane: Lane
    trouble: Trouble
    method: Method
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    history: list[str] = field(default_factory=list)
    facts: dict[str, str | int | float | bool] = field(default_factory=dict)

    def add(self, key: str, ent: Entity) -> Entity:
        self.entities[key] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def note(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(part for part in para if part) for para in self.paragraphs if para)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(
            f"lane={self.lane.key} trouble={self.trouble.key} method={self.method.key} "
            f"hero={self.params.hero} gender={self.params.gender}"
        )
        for key, ent in self.entities.items():
            meters = ", ".join(f"{k}={v}" for k, v in sorted(ent.meters.items()))
            memes = ", ".join(f"{k}={v}" for k, v in sorted(ent.memes.items()))
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            detail = "; ".join(part for part in (meters, memes, tags) if part)
            rows.append(f"  {key:<10} ({ent.kind:<10}/{ent.type:<8}) {detail}".rstrip())
        rows.append(f"  facts: {self.facts}")
        rows.append("  history:")
        rows.extend(f"    - {item}" for item in self.history)
        return "\n".join(rows)


LANES: dict[str, Lane] = {
    "brook_stones": Lane(
        key="brook_stones",
        phrase="the brook-stone bend by the willow rail",
        landmark="A willow rail leaned over the water like a sleepy shepherd's crook",
        light=1,
        footing=1,
        reach_anchor=1,
        dry_bank=0,
        ending_view="the brook wore penny-bright ripples and the willow leaves stopped shivering",
    ),
    "lantern_steps": Lane(
        key="lantern_steps",
        phrase="the lantern steps beside the cottage wall",
        landmark="A brass lantern buttoned a warm circle onto the pale wall",
        light=2,
        footing=2,
        reach_anchor=0,
        dry_bank=1,
        ending_view="the cottage steps glowed like warm toast in the late gold light",
    ),
    "berry_gate": Lane(
        key="berry_gate",
        phrase="the berry gate at the end of the garden lane",
        landmark="Round berries bobbed on the hedge and made the gate look like a jam tart",
        light=0,
        footing=2,
        reach_anchor=1,
        dry_bank=1,
        ending_view="the berry gate stood still and sweet, with no branch tugging at all",
    ),
    "hay_cart_yard": Lane(
        key="hay_cart_yard",
        phrase="the hay-cart yard behind the red shed",
        landmark="A low cart of hay sat there as soft as a lion made of straw",
        light=1,
        footing=0,
        reach_anchor=2,
        dry_bank=2,
        ending_view="the hay cart held its straw in tidy curls under the mild blue sky",
    ),
}

TROUBLES: dict[str, Trouble] = {
    "duckling_puddle": Trouble(
        key="duckling_puddle",
        creature_type="duckling",
        creature_phrase="the duckling",
        scene_text="A duckling stood on a tilted pail by a puddle and peeped as if the shiny splash were a whole deep sea.",
        fear_cause="the water looked colder and wider than it truly was",
        obstacle="the tilted pail and the cold puddle",
        safe_place="the dry path",
        resolve_text="Soon the duckling tucked its beak, took one brave hop, and pattered from the tilted pail to the dry path.",
        ending_image="The duckling paddled through the thin edge of the puddle and made little silver rings around its toes.",
        lesson="A brave heart grows when one small step follows one kind rhyme.",
        fear_need=1,
        light_need=0,
        reach_need=1,
        steady_need=1,
        burr_need=0,
        splash_need=1,
    ),
    "lamb_burrs": Trouble(
        key="lamb_burrs",
        creature_type="lamb",
        creature_phrase="the lamb",
        scene_text="A lamb had backed into the berry hedge, and burrs sat in its wool like cross little buttons.",
        fear_cause="the hedge kept catching and scratching at every wiggle",
        obstacle="the burry hedge",
        safe_place="the open lane",
        resolve_text="Soon the burrs came loose one by one, and the lamb skipped backward into the open lane with a soft snort.",
        ending_image="The lamb trotted in two neat circles, and the hedge stopped shaking its leaves.",
        lesson="Bravery can look gentle when patient hands untangle what fear has tightened.",
        fear_need=1,
        light_need=0,
        reach_need=1,
        steady_need=1,
        burr_need=1,
        splash_need=0,
    ),
    "mouse_boat": Trouble(
        key="mouse_boat",
        creature_type="mouse",
        creature_phrase="the mouse",
        scene_text="A mouse in a walnut-shell boat kept spinning by the reeds and squeaked every time the boat kissed the bank and slipped away again.",
        fear_cause="the little boat would not stay still long enough for safe paws",
        obstacle="the spinning walnut boat",
        safe_place="the bank",
        resolve_text="Soon the walnut boat nudged in close, and the mouse stepped onto the bank with both tiny paws held high and dry.",
        ending_image="The walnut boat slept by the shore while the mouse nibbled a seed no bigger than a moon crumb.",
        lesson="Even when the world spins, a steady rhyme can make the next move plain.",
        fear_need=2,
        light_need=0,
        reach_need=2,
        steady_need=1,
        burr_need=0,
        splash_need=1,
    ),
    "chick_shadow": Trouble(
        key="chick_shadow",
        creature_type="chick",
        creature_phrase="the chick",
        scene_text="A chick had tucked itself under a step where the shadow looked twice as wide as the space beneath it.",
        fear_cause="the dark corner made a tiny place seem too large and strange",
        obstacle="the broad shadow under the step",
        safe_place="the bright step",
        resolve_text="Soon the chick blinked at the kinder light and pattered out from under the step to the bright stone.",
        ending_image="The chick pecked at crumbs in the sunshine, and the shadow looked no bigger than a folded mitten.",
        lesson="A little light and a brave song can shrink a great big fear back to its true size.",
        fear_need=1,
        light_need=2,
        reach_need=0,
        steady_need=0,
        burr_need=0,
        splash_need=0,
    ),
}

METHODS: dict[str, Method] = {
    "glow_pebble_song": Method(
        key="glow_pebble_song",
        phrase="a glow-pebble song",
        pocket_item="a glow pebble",
        brave_rhyme="Glow and go, soft and slow; small feet know the way to go.",
        action_text="lifted the glow pebble high so its shy light could smooth the edges of the worry",
        calm_boost=1,
        light_boost=2,
        reach_boost=0,
        steady_boost=0,
        burr_help=0,
    ),
    "button_string_loop": Method(
        key="button_string_loop",
        phrase="a button-string loop",
        pocket_item="a button tied to a spool of string",
        brave_rhyme="Loop and lean, neat and keen; brave can be both small and clean.",
        action_text="swung a string loop from the pocket button and reached it out with slow, careful hands",
        calm_boost=0,
        light_boost=0,
        reach_boost=2,
        steady_boost=1,
        burr_help=2,
    ),
    "oat_crumb_trail": Method(
        key="oat_crumb_trail",
        phrase="an oat-crumb trail",
        pocket_item="a paper twist of oat crumbs",
        brave_rhyme="Crumb by crumb, do not run; gentle steps can still get done.",
        action_text="laid oat crumbs in a tidy line and waited for calm to do its quiet work",
        calm_boost=2,
        light_boost=0,
        reach_boost=0,
        steady_boost=0,
        burr_help=0,
    ),
    "tin_spoon_tap": Method(
        key="tin_spoon_tap",
        phrase="a tin-spoon tap",
        pocket_item="a tin spoon",
        brave_rhyme="Tap and tread, clear the dread; one kind beat goes on ahead.",
        action_text="tapped a tiny spoon-beat and stepped to it so the rescue could move in time instead of in fright",
        calm_boost=1,
        light_boost=0,
        reach_boost=1,
        steady_boost=2,
        burr_help=1,
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Marnie", "Tilly", "Nora", "Poppy"),
    "boy": ("Tobin", "Milo", "Jory", "Finn"),
    "child": ("Pip", "Sunny", "Robin", "Wren"),
}

CURATED: list[StoryParams] = [
    StoryParams("brook_stones", "duckling_puddle", "tin_spoon_tap", "Marnie", "girl", 4101),
    StoryParams("berry_gate", "lamb_burrs", "button_string_loop", "Tobin", "boy", 4102),
    StoryParams("hay_cart_yard", "mouse_boat", "tin_spoon_tap", "Pip", "child", 4103),
    StoryParams("lantern_steps", "chick_shadow", "glow_pebble_song", "Nora", "girl", 4104),
    StoryParams("hay_cart_yard", "duckling_puddle", "oat_crumb_trail", "Milo", "boy", 4105),
]


def reasonableness_report(lane: Lane, trouble: Trouble, method: Method) -> tuple[bool, str]:
    calm_total = method.calm_boost + min(lane.light, 1)
    if calm_total < trouble.fear_need:
        return False, "the child would still be too frightened or the creature too startled to begin"

    if lane.light + method.light_boost < trouble.light_need:
        return False, "there is not enough light to make the scary place look safe and understandable"

    if lane.reach_anchor + method.reach_boost < trouble.reach_need:
        return False, "the child could not reach the trouble safely from this lane with this pocket tool"

    if lane.footing + method.steady_boost < trouble.steady_need:
        return False, "the footing is too wobbly for a careful nursery-rhyme rescue"

    if lane.reach_anchor + method.burr_help < trouble.burr_need:
        return False, "the child has no good way to loosen the snagging burrs"

    if lane.dry_bank + method.steady_boost < trouble.splash_need:
        return False, "the rescue would end in too much splashing and slipping"

    return True, ""


def valid_combos() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for lane in LANES.values():
        for trouble in TROUBLES.values():
            for method in METHODS.values():
                ok, _ = reasonableness_report(lane, trouble, method)
                if ok:
                    rows.append((lane.key, trouble.key, method.key))
    return rows


def explain_rejection(args: argparse.Namespace) -> str:
    if not all([args.lane, args.trouble, args.method]):
        return "(No valid combinations match the requested options.)"
    ok, reason = reasonableness_report(LANES[args.lane], TROUBLES[args.trouble], METHODS[args.method])
    if ok:
        return "(No valid combinations match the requested options.)"
    return f"(No story: {reason})"


def pocket_intro(method: Method) -> str:
    return f"{method.pocket_item} tucked in the right trouser pocket"


def build_world(params: StoryParams) -> World:
    lane = LANES[params.lane]
    trouble = TROUBLES[params.trouble]
    method = METHODS[params.method]
    ok, reason = reasonableness_report(lane, trouble, method)
    if not ok:
        raise StoryError(reason)

    world = World(params=params, lane=lane, trouble=trouble, method=method)
    hero = world.add("Hero", Entity(name=params.hero, kind="character", type=params.gender))
    creature = world.add("Creature", Entity(name=trouble.creature_phrase, kind="creature", type=trouble.creature_type))
    trouser = world.add("Trouser", Entity(name="patchwork trousers", kind="garment", type="trousers"))
    pocket = world.add("PocketItem", Entity(name=method.pocket_item, kind="tool", type="pocket_item"))
    place = world.add("Place", Entity(name=lane.phrase, kind="place", type="lane"))

    hero.set_meter("worry", float(trouble.fear_need))
    hero.set_meter("courage", 0.0)
    creature.set_meter("fear", float(trouble.fear_need))
    creature.set_meter("safe", 0.0)
    trouser.set_meter("wet_cuff", 0.0)
    trouser.set_meter("burr_count", 0.0)
    pocket.set_meter("used", 0.0)
    place.set_meter("peace", 0.0)

    world.say(
        f"On {lane.phrase}, {hero.name} came in patchwork trousers, with {pocket_intro(method)}."
    )
    world.say(f"{lane.landmark}.")
    world.say(trouble.scene_text)
    hero.add_meme("care", 1.0)
    creature.add_meme("need", 1.0)
    world.note(f"premise: {hero.name} sees {trouble.creature_phrase} at {lane.key}")

    world.para()
    world.say(
        f"{hero.name} felt a thump-thump in {hero.pronoun('possessive')} chest, because {trouble.fear_cause}."
    )
    world.say(
        f"Still, {hero.pronoun('subject')} touched the right trouser pocket and sang, \"{method.brave_rhyme}\""
    )
    hero.add_meter("courage", 2.0)
    hero.add_meter("worry", -1.0)
    hero.add_meme("bravery", 2.0)
    pocket.add_meter("used", 1.0)
    world.facts["rhyme_used"] = method.brave_rhyme
    world.note(f"turn: {hero.name} chooses {method.key}")

    world.para()
    world.say(f"Then {hero.name} {method.action_text}.")

    if trouble.light_need:
        world.say("The dim place lost its giant look once the edge of it could be seen.")
    if trouble.splash_need:
        trouser.add_meter("wet_cuff", 1.0)
        world.say(f"A cool kiss of splash touched the trouser cuff, but {hero.name} did not scamper away.")
    if trouble.burr_need:
        trouser.add_meter("burr_count", 1.0)
        world.say(f"One burr ticked against the trouser knee, yet {hero.name} kept the hands slow and kind.")

    hero.add_meter("courage", 1.0)
    creature.add_meter("fear", -float(trouble.fear_need))
    world.say(trouble.resolve_text)
    world.note(f"resolution move: {trouble.creature_phrase} leaves {trouble.obstacle} for {trouble.safe_place}")

    world.para()
    creature.set_meter("safe", 1.0)
    creature.add_meme("relief", 2.0)
    hero.add_meme("joy", 2.0)
    place.set_meter("peace", 2.0)
    world.facts["resolved"] = True
    world.facts["ending_image"] = trouble.ending_image
    world.facts["happy_place"] = lane.ending_view
    world.say(f"{trouble.lesson}")
    world.say(f"{trouble.ending_image} Beside it, {lane.ending_view}.")
    world.say(
        f"{hero.name} gave the right trouser pocket a grateful pat, for the brave little rescue had turned the whole place mild and merry."
    )
    world.note("ending: happy image proved by safe creature, quiet place, and relieved child")
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a nursery-rhyme style story that includes the word trouser.",
        f"Set it on {world.lane.phrase} and make the danger child-sized rather than huge.",
        f"Let {world.params.hero} use {world.method.pocket_item} and a brave rhyme to help {world.trouble.creature_phrase}, then finish with a concrete happy ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.entities["Hero"]
    return [
        (
            "Where does the story happen?",
            f"It happens on {world.lane.phrase}. The place matters because its light, footing, and edges shape how the brave rescue can work.",
        ),
        (
            "What trouble did the child find?",
            f"{hero.name} found {world.trouble.creature_phrase} in trouble with {world.trouble.obstacle}. That problem looked bigger than it really was, so it gave the story its moment of fear.",
        ),
        (
            "What was in the trouser pocket, and why did it matter?",
            f"The right trouser pocket held {world.method.pocket_item}. It mattered because that simple thing matched the problem closely enough to turn worry into a useful plan.",
        ),
        (
            "How did the child show bravery?",
            f"{hero.name} felt afraid and still moved forward instead of running away. The brave rhyme helped {hero.pronoun('object')} act slowly, kindly, and on purpose.",
        ),
        (
            "How was the creature helped?",
            f"{hero.name} used {world.method.phrase} until {world.trouble.resolve_text.lower()} That changed the creature's state from frightened and stuck to calm and safe.",
        ),
        (
            "What proves the ending is happy?",
            f"The story ends with a visible proof image: {world.trouble.ending_image} The lane looks peaceful too, so the child, the creature, and the place have all changed for the better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    rows = [
        (
            "Why can a rhyme help a child be brave?",
            "A rhyme gives the body a small steady beat to follow. That makes fear feel less wild and helps the next careful action arrive in order.",
        ),
        (
            "Why can a pocket object matter in a tiny rescue story?",
            "A pocket object is small enough for a child to carry and choose alone. That makes the brave turn feel personal instead of borrowed from a grown-up.",
        ),
        (
            "Why is gentleness important when helping a scared animal?",
            "Scared animals notice speed and noise very quickly. Gentle hands and gentle timing make it easier for them to trust the path to safety.",
        ),
    ]
    if world.trouble.splash_need:
        rows.append(
            (
                "Why do slow feet matter near puddles or water?",
                "Water makes edges slick and makes frightened creatures hesitate. Slow feet keep both balance and trust from tipping away.",
            )
        )
    if world.trouble.burr_need:
        rows.append(
            (
                "Why is patience useful when something is tangled in burrs?",
                "Burrs cling harder when a body jerks against them. Patience loosens them bit by bit instead of turning a small snag into a bigger one.",
            )
        )
    if world.trouble.light_need:
        rows.append(
            (
                "Why can light make a small fear shrink?",
                "Shadows often look larger than the true space they cover. When the edges become visible, the mind can measure the problem properly.",
            )
        )
    return rows


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for lane in LANES.values():
        rows.append(
            asp.fact(
                "lane",
                lane.key,
                lane.light,
                min(lane.light, 1),
                lane.footing,
                lane.reach_anchor,
                lane.dry_bank,
            )
        )
    for trouble in TROUBLES.values():
        rows.append(
            asp.fact(
                "trouble",
                trouble.key,
                trouble.fear_need,
                trouble.light_need,
                trouble.reach_need,
                trouble.steady_need,
                trouble.burr_need,
                trouble.splash_need,
            )
        )
    for method in METHODS.values():
        rows.append(
            asp.fact(
                "method",
                method.key,
                method.calm_boost,
                method.light_boost,
                method.reach_boost,
                method.steady_boost,
                method.burr_help,
            )
        )
    return "\n".join(rows)


ASP_RULES = r"""
valid(L, T, M) :-
    lane(L, Light, LightFlag, Footing, ReachAnchor, DryBank),
    trouble(T, FearNeed, LightNeed, ReachNeed, SteadyNeed, BurrNeed, SplashNeed),
    method(M, CalmBoost, LightBoost, ReachBoost, SteadyBoost, BurrHelp),
    CalmTotal = CalmBoost + LightFlag,
    CalmTotal >= FearNeed,
    Light + LightBoost >= LightNeed,
    ReachAnchor + ReachBoost >= ReachNeed,
    Footing + SteadyBoost >= SteadyNeed,
    ReachAnchor + BurrHelp >= BurrNeed,
    DryBank + SteadyBoost >= SplashNeed.

#show valid/3.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nursery-rhyme bravery storyworld with a trouser-pocket rescue.")
    parser.add_argument("--lane", choices=sorted(LANES))
    parser.add_argument("--trouble", choices=sorted(TROUBLES))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("-n", type=int, default=1, help="number of stories")
    parser.add_argument("--all", action="store_true", help="render a curated story set")
    parser.add_argument("--seed", type=int, default=None, help="base seed for random choices")
    parser.add_argument("--trace", action="store_true", help="print world model state after each story")
    parser.add_argument("--qa", action="store_true", help="include prompts and grounded QA")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of prose")
    parser.add_argument("--asp", action="store_true", help="list compatible (lane, trouble, method) combinations")
    parser.add_argument("--verify", action="store_true", help="compare Python and ASP reasoning and exercise generated stories")
    parser.add_argument("--show-asp", action="store_true", help="print the inline ASP rules and emitted facts")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (args.lane is None or combo[0] == args.lane)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError(explain_rejection(args))

    lane_key, trouble_key, method_key = rng.choice(combos)
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero_pool = HERO_NAMES[gender]
    hero = args.hero or rng.choice(hero_pool)
    return StoryParams(
        lane=lane_key,
        trouble=trouble_key,
        method=method_key,
        hero=hero,
        gender=gender,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    if (params.lane, params.trouble, params.method) not in valid_combos():
        fake = argparse.Namespace(lane=params.lane, trouble=params.trouble, method=params.method)
        raise StoryError(explain_rejection(fake))
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("")
        print(sample.world.trace())
    if qa and sample.world is not None:
        print("")
        print(format_qa(sample))


def exercise_generated_stories() -> list[str]:
    problems: list[str] = []
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            lane=combo[0],
            trouble=combo[1],
            method=combo[2],
            hero="Marnie",
            gender="girl",
            seed=6200 + i,
        )
        sample = generate(params)
        story = sample.story.lower()
        if "trouser" not in story:
            problems.append(f"{combo}: story is missing the seed word 'trouser'")
        if "brave" not in story:
            problems.append(f"{combo}: story is missing explicit bravery language")
        if sample.story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, turn, or ending paragraph")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world QA set is too small")
        if any(answer.answer.count(".") < 2 for answer in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
        if sample.world is None:
            problems.append(f"{combo}: missing world model")
            continue
        hero = sample.world.entities["Hero"]
        creature = sample.world.entities["Creature"]
        place = sample.world.entities["Place"]
        if hero.memes.get("bravery", 0.0) <= 0.0:
            problems.append(f"{combo}: bravery state was not recorded")
        if creature.meters.get("safe") != 1.0:
            problems.append(f"{combo}: creature never reached a safe state")
        if place.meters.get("peace") != 2.0:
            problems.append(f"{combo}: place did not reach its peaceful end state")
        if not sample.world.facts.get("resolved"):
            problems.append(f"{combo}: world facts do not mark the story resolved")
    return problems


def asp_verify() -> int:
    py = set(valid_combos())
    logic = set(asp_valid_combos())
    status = 0
    if py == logic:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between Python and ASP gate")
        if py - logic:
            print(f"  only python: {sorted(py - logic)}")
        if logic - py:
            print(f"  only asp: {sorted(logic - py)}")
        status = 1

    problems = exercise_generated_stories()
    if problems:
        print("Story exercise failures:")
        for item in problems:
            print(f"  {item}")
        status = 1
    else:
        print("OK: generated stories pass seed, state, QA, and happy-ending checks.")
    return status


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    attempts = 0
    while len(samples) < target and attempts < target * 60:
        seed = base_seed + attempts
        attempts += 1
        local = argparse.Namespace(**vars(args))
        local.seed = seed
        params = resolve_params(local, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Not enough unique trouser-pocket stories from the current constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    if args.lane or args.trouble or args.method:
        combos = [
            combo
            for combo in valid_combos()
            if (args.lane is None or combo[0] == args.lane)
            and (args.trouble is None or combo[1] == args.trouble)
            and (args.method is None or combo[2] == args.method)
        ]
        if not combos:
            raise StoryError(explain_rejection(args))
        base_seed = args.seed if args.seed is not None else 7300
        rows: list[StorySample] = []
        for i, combo in enumerate(combos):
            gender = args.gender or "child"
            hero = args.hero or HERO_NAMES[gender][0]
            params = StoryParams(combo[0], combo[1], combo[2], hero, gender, base_seed + i)
            rows.append(generate(params))
        return rows
    return [generate(params) for params in CURATED]


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    try:
        samples = _sample_all(args) if args.all else _sample_n(args)
    except StoryError as exc:
        build_parser().error(str(exc))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.trouble}/{p.method}/{p.lane}"
        elif len(samples) > 1:
            header = f"### variant {i + 1} seed={sample.params.seed}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
