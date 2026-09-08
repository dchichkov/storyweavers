#!/usr/bin/env python3
"""
Wildebeest mystery adventure: a missing market bell and an honest sale.

A small classical story simulation about a young wildebeest who wants to sell
handmade reed whistles, but must solve a market mystery before the sale can
begin.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Wildebeest:
    name: str
    role: str
    kind: str = "animal"
    meters: dict[str, float] = field(default_factory=lambda: {"energy": 1.0, "curiosity": 0.5})
    memes: dict[str, float] = field(
        default_factory=lambda: {"courage": 0.2, "honesty": 0.5, "worry": 0.2}
    )
    inventory: list[str] = field(default_factory=list)


@dataclass
class MarketObject:
    name: str
    material: str
    owner: str
    location: str
    found: bool = False
    returned: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"usefulness": 1.0})
    memes: dict[str, float] = field(default_factory=lambda: {"trust": 0.5})


@dataclass
class Setting:
    place: str = "the red-dust market"
    description: str = "a busy clearing beneath acacia trees where travelers trade useful things"


@dataclass
class StoryParams:
    place: str = "the red-dust market"
    hero_name: str = "Luma"
    companion_name: str = "Tavi"
    stall_keeper_name: str = "Bako"
    mystery_id: int = 0
    opening_mode: int = 0
    clue_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Mystery:
    premise: str
    problem: str
    first_attempt: str
    clue: str
    discovery: str
    action: str
    resolution: str
    lesson: str
    ending: str


MYSTERIES = (
    Mystery(
        premise="Luma had made a bundle of bright reed whistles and carried them to the market to sell.",
        problem="The market bell that opened every fair sale had vanished from Bako's table, and nobody knew whether the morning trade could begin.",
        first_attempt="searched under the cloths and baskets without telling anyone",
        clue="a line of tiny hoofprints led from the table toward a dry streambed",
        discovery="the bell had been carried away by a curious young zebra who thought it was a shiny seed pod",
        action="followed the hoofprints while Tavi asked nearby traders what they had seen",
        resolution="They found the bell caught in thorny grass, explained the mistake kindly, and returned it before the market opened.",
        lesson="a mystery is solved best when careful eyes and honest questions work together",
        ending="the bell rang above the stalls, and Luma sold the first whistle to a smiling traveler",
    ),
    Mystery(
        premise="Luma brought painted gourds to sell at the traveling market after practicing her prices all week.",
        problem="The pouch holding the stall tokens disappeared just before traders were meant to choose their places.",
        first_attempt="blamed the wind and stuffed every loose cloth into a basket",
        clue="one blue token glimmered beside a patch of flattened grass",
        discovery="the tokens had spilled from a torn pouch when a hyena pup tugged at its bright tassel",
        action="marked the trail with pebbles while Tavi invited the pup's keeper to help search",
        resolution="They gathered every token, mended the pouch, and gave the frightened pup a painted gourd to hold.",
        lesson="a calm search can uncover the truth without making an innocent neighbor feel small",
        ending="the repaired pouch hung safely at the stall while customers admired the painted gourds",
    ),
    Mystery(
        premise="Luma had woven strong grass bracelets to sell beside the river road.",
        problem="A customer's silver bead was missing, and the customer feared it had fallen among Luma's bracelets.",
        first_attempt="offered to give away every bracelet before checking what had happened",
        clue="the bead's faint rattle came from inside a hollow calabash",
        discovery="a gust had rolled the bead into the calabash while Luma was arranging her goods",
        action="held the calabash still while Tavi tipped it gently over a clean cloth",
        resolution="The bead was returned, and the customer bought one bracelet because Luma had treated the worry with care.",
        lesson="honest help can turn a frightening mistake into lasting trust",
        ending="the bracelet shone around the customer's wrist as the river flashed behind the stall",
    ),
    Mystery(
        premise="Luma traveled with a small herd to sell bundles of sweet-smelling salt grass.",
        problem="The best bundle was missing its red marker, so no one could tell which buyer had reserved it.",
        first_attempt="quietly moved the bundle toward her own mat",
        clue="red fibers clung to the thorn bush beside the water jars",
        discovery="a baboon had dragged the marker away while searching for a drink",
        action="followed the fibers and asked the water keeper whether the baboon had been seen",
        resolution="They found the marker near the jars, replaced it, and delivered the reserved bundle to its buyer.",
        lesson="doing the fair thing matters even when a shortcut would bring a quick reward",
        ending="the buyer carried the marked grass home, and Luma's own stall stood proudly empty",
    ),
    Mystery(
        premise="Luma made a little map of safe watering places and hoped to sell copies to travelers.",
        problem="The master map vanished from the signboard, leaving the travelers unsure which trail was safe.",
        first_attempt="said she could redraw it from memory, though several paths looked alike",
        clue="a corner of the map was pinned beneath a sleeping tortoise's shell",
        discovery="the morning wind had lifted the map, and the tortoise had sheltered it by accident",
        action="waited quietly for the tortoise to move while Tavi held the signboard steady",
        resolution="They recovered the map, weighted the corners with stones, and sold only copies checked against the original.",
        lesson="good work includes checking what you think you know",
        ending="travelers followed the marked trail while Luma's careful maps earned warm thanks",
    ),
    Mystery(
        premise="Luma carried polished bone buttons to sell at a cloth-maker's camp.",
        problem="The button maker's measuring cord disappeared, so nobody could tell whether the buttons were the promised size.",
        first_attempt="pretended the cord was unimportant and began naming prices",
        clue="a fresh groove crossed the dust between the measuring mat and a wagon wheel",
        discovery="the cord had caught on the wheel and been dragged beneath the wagon",
        action="crawled beneath the wagon with Tavi holding a lantern made from a shaded firefly jar",
        resolution="They freed the cord, measured the buttons honestly, and sorted the ones that needed a different price.",
        lesson="a fair sale depends on clear facts, not confident pretending",
        ending="the sorted buttons filled three neat trays beneath the wagon's bright awning",
    ),
    Mystery(
        premise="Luma planned to sell woven seed bags at the edge of a grassland festival.",
        problem="The festival's first prize ribbon disappeared, and the judges feared someone had taken it.",
        first_attempt="hid her own seed bags so nobody would suspect her",
        clue="a strip of gold thread hung from the festival drum",
        discovery="the ribbon had tangled around the drum when the drummer carried it through the tall grass",
        action="followed the gold thread and asked the drummer to retrace the morning route",
        resolution="They untangled the ribbon and cleared every seller, including Luma, of suspicion.",
        lesson="speaking up with useful clues protects everyone from unfair blame",
        ending="the prize ribbon fluttered above the drum while seed bags changed hands below",
    ),
    Mystery(
        premise="Luma shaped small clay cups and came to sell them before sunset.",
        problem="One cup cracked on the journey, and the customer who ordered it believed Luma had hidden the damage.",
        first_attempt="turned the cracked side toward the wall",
        clue="the crack was warm and dusty, showing it had happened on the road",
        discovery="the cup had broken before reaching the market, but Luma could still offer a safe replacement",
        action="showed the crack openly while Tavi brought clay from a nearby potter",
        resolution="Luma replaced the cup and marked the damaged one for repair instead of selling it as new.",
        lesson="honesty makes a small loss safer than a hidden disappointment",
        ending="a repaired cup cooled beside the stall while the customer carried home a sound one",
    ),
    Mystery(
        premise="Luma gathered blue feathers to sell for festival fans.",
        problem="The feather basket was lighter than it should have been, and a child nearby was holding one of the missing feathers.",
        first_attempt="stared angrily at the child and reached for the feather",
        clue="the child pointed to a broken basket handle near the path",
        discovery="the feathers had blown out, and the child had only picked up one to return it",
        action="thanked the child and followed the scattered feathers with Tavi along the fence",
        resolution="They recovered most of the feathers, repaired the handle, and gave the child a small fan.",
        lesson="asking before accusing can reveal a helper instead of creating an enemy",
        ending="the child waved the new fan as blue feathers danced safely inside the mended basket",
    ),
    Mystery(
        premise="Luma prepared fragrant herbs to sell to cooks at the evening market.",
        problem="The labels on two herb bundles were mixed up, and selling them wrongly could spoil a customer's meal.",
        first_attempt="guessed from the colors and arranged the bundles quickly",
        clue="one bundle smelled sharp while the other carried a warm lemon scent",
        discovery="the labels had fallen when a goat brushed the table, but the herbs could be identified by smell",
        action="asked the cooks to smell a sample while Tavi found the fallen labels under the table",
        resolution="They matched each label correctly and warned buyers not to rely on color alone.",
        lesson="when a choice matters, patient checking is wiser than a fast guess",
        ending="the evening cooks carried home the right herbs, and Luma's stall smelled like a garden",
    ),
    Mystery(
        premise="Luma brought strong vine ropes to sell to travelers repairing a bridge.",
        problem="A coil of rope seemed shorter than the promised length, and the bridge crew refused to buy it.",
        first_attempt="pulled the rope tight and insisted it looked long enough",
        clue="a knot near the center hid a loop folded inside the coil",
        discovery="the rope was the correct length, but it had been coiled carelessly around a hidden loop",
        action="unwound the coil with Tavi while the bridge crew watched every section",
        resolution="They measured the rope from end to end, retied it clearly, and agreed on a fair price.",
        lesson="trust grows when people can see how a claim has been checked",
        ending="the measured rope strengthened the bridge while Luma counted the honest coins",
    ),
    Mystery(
        premise="Luma painted tiny signs to sell to travelers who could not read the market paths.",
        problem="The sign marked 'water' pointed toward the empty shade tent instead of the well.",
        first_attempt="turned the sign around and hoped nobody would notice",
        clue="the sign's bottom edge bore fresh scratches from being dragged across the ground",
        discovery="a young camel had pulled the sign from its post while looking for shade",
        action="followed the drag marks and asked the well keeper to check the true direction",
        resolution="They moved the sign beside the well and added a clear blue drop beneath the word.",
        lesson="fixing a confusing mistake helps more people than quietly hiding it",
        ending="thirsty travelers followed the blue drop and found the cool well",
    ),
)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, eid: str, entity: object) -> object:
        self.entities[eid] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _render(text: str, hero: Wildebeest, companion: Wildebeest) -> str:
    return text.format(hero=hero.name, companion=companion.name)


def _place_phrase(place: str) -> str:
    lower = place.lower()
    if lower.startswith(("in ", "at ", "on ", "beside ")):
        return place
    return f"at {place}"


def tell(params: StoryParams) -> World:
    if not params.hero_name.strip() or not params.companion_name.strip():
        raise StoryError("hero and companion names must not be empty")
    if params.mystery_id < 0 or params.mystery_id >= len(MYSTERIES):
        raise StoryError("mystery_id must select an available market mystery")

    world = World(Setting(place=params.place))
    hero = world.add(
        "hero",
        Wildebeest(name=params.hero_name, role="seller"),
    )
    companion = world.add(
        "companion",
        Wildebeest(name=params.companion_name, role="helper"),
    )
    keeper = world.add(
        "keeper",
        Wildebeest(name=params.stall_keeper_name, role="market keeper"),
    )
    goods = world.add(
        "goods",
        MarketObject(
            name="handmade goods",
            material="reed, clay, grass, or other gathered material",
            owner=hero.name,
            location=world.setting.place,
        ),
    )
    mystery = MYSTERIES[params.mystery_id]

    hero.inventory.append("handmade goods")
    hero.meters["energy"] = 0.9
    hero.memes["worry"] = 0.35

    openings = (
        f"At {_place_phrase(world.setting.place)}, {hero.name} the wildebeest arranged a small stall beneath an acacia tree.",
        f"The adventure began {_place_phrase(world.setting.place)}, where {hero.name} the wildebeest hoped to sell something made with patient work.",
        f"Before the market grew busy, {hero.name} the wildebeest and {companion.name} the wildebeest reached {_place_phrase(world.setting.place)}.",
        f"Sunlight spilled across {_place_phrase(world.setting.place)} as {hero.name} unpacked goods for the day's sale.",
        f"{hero.name} had crossed the grassland to sell at {_place_phrase(world.setting.place)}, with {companion.name} walking beside the loaded cart.",
        f"A lively market waited {_place_phrase(world.setting.place)}. {hero.name} stood ready to sell, but the morning had prepared a different adventure.",
    )
    world.say(openings[params.opening_mode % len(openings)])
    world.say(_render(mystery.premise, hero, companion))
    world.say(
        f"'{companion.name}, will you help me check the stall?' asked {hero.name}. "
        f"'I will,' said {companion.name}. 'A good sale should begin with a clear mind.'"
    )

    world.para()
    world.say(_render(mystery.problem, hero, companion))
    world.say(f"At first, {hero.name} {_render(mystery.first_attempt, hero, companion)}.")
    world.say(
        f"'{hero.name}, do not guess yet,' said {companion.name}. "
        f"'What small thing does not belong?'"
    )
    world.say(f"{hero.name} took a breath. 'You are right. We need a clue before we decide.'")

    world.para()
    clues = (
        f"Together they noticed that {_render(mystery.clue, hero, companion)}.",
        f"The first useful clue appeared when {_render(mystery.clue, hero, companion)}.",
        f"{companion.name} pointed carefully. {_render(mystery.clue, hero, companion)}.",
        f"After looking instead of rushing, {hero.name} saw that {_render(mystery.clue, hero, companion)}.",
    )
    world.say(clues[params.clue_mode % len(clues)])
    world.say(f"That clue led them to understand that {_render(mystery.discovery, hero, companion)}.")
    world.say(f"'{companion.name}, I know what to do now,' said {hero.name}.")
    world.say(f"'Then let us do it together,' replied {companion.name}.")
    world.say(f"{hero.name} {_render(mystery.action, hero, companion)}.")
    world.say(_render(mystery.resolution, hero, companion))

    goods.found = True
    goods.returned = True
    goods.location = world.setting.place
    hero.meters["energy"] = max(0.0, hero.meters["energy"] - 0.25)
    hero.memes["courage"] = 1.0
    hero.memes["honesty"] = 1.0
    hero.memes["worry"] = 0.0
    companion.memes["courage"] = 0.8
    companion.memes["honesty"] = 1.0
    world.events.extend(["problem_noticed", "question_asked", "clue_found", "mystery_solved", "sale_made"])

    world.para()
    endings = (
        f"{hero.name} learned that {_render(mystery.lesson, hero, companion)}",
        f"The mystery left {hero.name} with a lasting thought: {_render(mystery.lesson, hero, companion)}",
        f"On the walk home, {companion.name} reminded {hero.name} that {_render(mystery.lesson, hero, companion)}",
        f"{hero.name} no longer thought a fast answer was the bravest answer. {_render(mystery.lesson, hero, companion)}",
        f"The day's sale mattered, but the lesson mattered too: {_render(mystery.lesson, hero, companion)}",
        f"With the truth clear, {hero.name} understood that {_render(mystery.lesson, hero, companion)}",
    )
    world.say(endings[params.ending_mode % len(endings)] + ".")
    world.say(_render(mystery.ending, hero, companion) + ".")

    world.facts.update(
        hero=hero,
        companion=companion,
        keeper=keeper,
        goods=goods,
        mystery=mystery,
        problem=_render(mystery.problem, hero, companion),
        clue=_render(mystery.clue, hero, companion),
        discovery=_render(mystery.discovery, hero, companion),
        action=_render(mystery.action, hero, companion),
        resolution=_render(mystery.resolution, hero, companion),
        lesson=_render(mystery.lesson, hero, companion),
        ending=_render(mystery.ending, hero, companion),
        solved=True,
        sold=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero: Wildebeest = facts["hero"]
    companion: Wildebeest = facts["companion"]
    return [
        f"Write an adventure about {hero.name}, a wildebeest who wants to sell goods at {world.setting.place}, but faces this mystery: {facts['problem']}",
        f"Tell how {hero.name} and {companion.name} use this clue to solve a market mystery: {facts['clue']}",
        f"Write a child-facing adventure in which a wildebeest learns that {facts['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero: Wildebeest = facts["hero"]
    companion: Wildebeest = facts["companion"]
    goods: MarketObject = facts["goods"]
    return [
        QAItem(
            question=f"What mystery did {hero.name} and {companion.name} face?",
            answer=f"They had to solve this mystery before the sale: {facts['problem']}"
        ),
        QAItem(
            question=f"What clue helped {hero.name} solve the mystery?",
            answer=f"The important clue was that {facts['clue']}. It showed them that {facts['discovery']}."
        ),
        QAItem(
            question=f"How did {hero.name} and {companion.name} work together?",
            answer=f"{hero.name} {facts['action']}. Their teamwork helped return the missing object and make the market fair."
        ),
        QAItem(
            question=f"What happened to the goods {hero.name} brought to sell?",
            answer=f"The goods remained connected to {goods.owner}'s honest stall, and the mystery was solved before the sale began. By the end, {facts['ending']}."
        ),
        QAItem(
            question=f"What lesson did {hero.name} learn?",
            answer=f"{hero.name} learned that {facts['lesson']}. The solved mystery made that lesson real."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wildebeest?",
            answer="A wildebeest is a large African grazing animal with a sturdy body, curved horns, and a flowing mane."
        ),
        QAItem(
            question="What does it mean to sell something?",
            answer="To sell something means to give it to a buyer in exchange for money or another agreed payment."
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a question or puzzling problem whose answer can be found by noticing clues and reasoning carefully."
        ),
        QAItem(
            question="Why should a seller check goods honestly?",
            answer="A seller should check goods honestly so buyers know what they are receiving and can make a fair, safe choice."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
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


ASP_RULES = r"""
hero(H) :- wildebeest(H), seller(H).
helper(F) :- wildebeest(F), companion(F).
mystery_solved :- clue_found, question_asked, object_returned.
honest_sale :- mystery_solved, goods_checked, sold.
trust(H) :- honest_sale, hero(H).
safe_market :- mystery_solved.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("wildebeest", "hero"),
            asp.fact("wildebeest", "companion"),
            asp.fact("seller", "hero"),
            asp.fact("companion", "companion"),
            asp.fact("question_asked"),
            asp.fact("clue_found"),
            asp.fact("object_returned"),
            asp.fact("goods_checked"),
            asp.fact("sold"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1

    model = asp.one_model(
        asp_program(
            "#show hero/1. #show helper/1. #show mystery_solved/0. "
            "#show honest_sale/0. #show trust/1. #show safe_market/0."
        )
    )
    expected = {
        "hero": [("hero",)],
        "helper": [("companion",)],
        "mystery_solved": [()],
        "honest_sale": [()],
        "trust": [("hero",)],
        "safe_market": [()],
    }
    for predicate, tuples in expected.items():
        if set(asp.atoms(model, predicate)) != set(tuples):
            print(f"MISMATCH: ASP predicate {predicate} did not match expected parity.")
            return 1

    params = StoryParams(seed=17)
    sample = generate(params)
    required = ("mystery", "clue", "sell", "wildebeest")
    text = (sample.story + " " + " ".join(q.answer for q in sample.story_qa)).lower()
    if any(word not in text for word in required):
        print("MISMATCH: generated story did not exercise required narrative facts.")
        return 1

    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adventure storyworld about a wildebeest solving a mystery before a sale."
    )
    parser.add_argument("--place", default=None)
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
    places = [
        "the red-dust market",
        "the river-road market",
        "the acacia fair",
        "the grassland trading camp",
    ]
    return StoryParams(
        place=args.place or rng.choice(places),
        hero_name=rng.choice(["Luma", "Kito", "Nala", "Sefu", "Mara"]),
        companion_name=rng.choice(["Tavi", "Beni", "Paka", "Jori", "Ayo"]),
        stall_keeper_name=rng.choice(["Bako", "Deka", "Rami", "Sana", "Olu"]),
        mystery_id=rng.randrange(len(MYSTERIES)),
        opening_mode=rng.randrange(6),
        clue_mode=rng.randrange(4),
        ending_mode=rng.randrange(6),
        seed=args.seed,
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


def dump_trace(world: World) -> str:
    hero: Wildebeest = world.entities["hero"]
    companion: Wildebeest = world.entities["companion"]
    goods: MarketObject = world.entities["goods"]
    return "\n".join(
        [
            "--- world trace ---",
            f"place: {world.setting.place}",
            f"hero: {hero.name} role={hero.role} meters={hero.meters} memes={hero.memes}",
            f"companion: {companion.name} role={companion.role} meters={companion.meters} memes={companion.memes}",
            f"goods: owner={goods.owner} material={goods.material} found={goods.found} returned={goods.returned}",
            f"events: {', '.join(world.events)}",
        ]
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show hero/1. #show helper/1. #show mystery_solved/0. #show honest_sale/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        try:
            import asp
        except Exception as exc:  # pragma: no cover
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(
            asp_program("#show hero/1. #show helper/1. #show mystery_solved/0. #show honest_sale/0.")
        )
        print("hero:", asp.atoms(model, "hero"))
        print("helper:", asp.atoms(model, "helper"))
        print("mystery_solved:", asp.atoms(model, "mystery_solved"))
        print("honest_sale:", asp.atoms(model, "honest_sale"))
        return

    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(
                place="the red-dust market",
                hero_name="Luma",
                companion_name="Tavi",
                stall_keeper_name="Bako",
                mystery_id=i,
                opening_mode=i % 6,
                clue_mode=i % 4,
                ending_mode=i % 6,
            )
            for i in range(len(MYSTERIES))
        ]
    else:
        params_list = [
            resolve_params(args, random.Random(base_seed + index))
            for index in range(args.n)
        ]

    samples = [generate(params) for params in params_list]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
