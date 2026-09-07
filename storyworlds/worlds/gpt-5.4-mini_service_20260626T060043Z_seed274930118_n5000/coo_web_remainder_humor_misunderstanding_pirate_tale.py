#!/usr/bin/env python3
"""
A small pirate tale storyworld about a bird's coo, a sticky web, and the
remainder of a treasure share.

The core premise is a friendly misunderstanding aboard a tiny pirate ship:
the crew hears a coo in the rigging, mistakes the source, and discovers that
the "remainder" of the map isn't a leftover at all, but a clue hidden in a web.
The humor comes from the mix-up, and the resolution comes from the crew
carefully untangling what the sounds and scraps really mean.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPOSITORY_ROOT = os.path.dirname(STORYWORLDS_ROOT)
sys.path.insert(0, REPOSITORY_ROOT)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "sailor", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"captainess", "pirateess", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str = "the Wobblefin"
    setting: str = "on the little pirate ship"
    has_rigging: bool = True
    has_hold: bool = True


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mira"
    hero_type: str = "captain"
    mate_name: str = "Patch"
    mate_type: str = "pirate"
    bird_name: str = "Pip"
    bird_type: str = "seabird"
    scenario: int = 0
    route: int = 0


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        w = World(self.ship)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SCENARIOS = (
    {
        "title": "the breakfast count",
        "premise": "Three berry buns remained after breakfast, but the galley slate claimed four.",
        "mistake": "Patch blamed a tiny web above the cupboard, certain a spider had carried off the remainder.",
        "coo": "Pip cooed whenever the cupboard door swung open, which sounded suspiciously like a confession.",
        "failed": "They counted plates twice and even questioned a very innocent wooden spoon.",
        "clue": "a purple crumb on the ship's log and a web strand stuck harmlessly to its clasp",
        "cause": "a rolling bun had wedged beneath the closed log when the ship tilted",
        "action": "Mira held the slate while Patch retraced every serving and Pip pointed with one wing",
        "resolution": "They found the last bun, corrected the remainder to three, and saved the web by moving the log.",
        "joke": "The spoon received a formal apology and demanded a butter holiday.",
        "ending": "At dusk, three clean plates gleamed beside the untouched silver web.",
    },
    {
        "title": "the signal-flag remainder",
        "premise": "A red signal flag vanished just before the crew needed to greet a lighthouse keeper.",
        "mistake": "Mira thought Pip's urgent coo meant pirates were hiding beyond the fog.",
        "coo": "Pip was actually calling toward a web stretched between two folded flags.",
        "failed": "Patch waved the blue flag instead, accidentally announcing that the soup felt lonely.",
        "clue": "one red thread showing beneath the remaining flags",
        "cause": "the missing flag had folded around the others and caught on the edge of the web",
        "action": "Patch lowered the bundle while Mira followed the red thread without tearing the web",
        "resolution": "They freed the flag, left the spider's corner intact, and sent the proper greeting.",
        "joke": "The lighthouse keeper replied with a flag that meant, 'Please cheer up your soup.'",
        "ending": "The red flag snapped brightly above a web beaded with fog.",
    },
    {
        "title": "the divided treasure tokens",
        "premise": "The crew shared seventeen wooden treasure tokens among four sailors and puzzled over the remainder.",
        "mistake": "Patch heard Pip coo four times and declared that four tokens must be left.",
        "coo": "Pip was cooing at a loose feather resting in a web, not doing arithmetic.",
        "failed": "Their first piles were uneven, and Patch tried to make a token by painting a biscuit.",
        "clue": "four equal rows scratched in chalk with one token still outside them",
        "cause": "seventeen makes four groups of four with a remainder of one",
        "action": "Mira arranged the tokens in rows while everyone checked the count aloud",
        "resolution": "Each sailor received four tokens, and they placed the one-token remainder in the repair fund.",
        "joke": "Patch ate the painted biscuit before anyone could spend it.",
        "ending": "Four neat token rows shone below the little feathered web.",
    },
    {
        "title": "the bell-rope puzzle",
        "premise": "The watch bell rang once although no one had pulled its rope.",
        "mistake": "Mira mistook Pip's answering coo for a warning that the anchor had broken.",
        "coo": "Pip kept looking at a web beside the bell rather than toward the anchor.",
        "failed": "Patch inspected the anchor chain and returned wearing a bucket like a helmet.",
        "clue": "a loose remainder of rope brushing the bell whenever the sail filled",
        "cause": "the trimmed end of the new bell rope had not been tied back",
        "action": "Mira watched one gust, then asked Patch to secure the loose end well away from the web",
        "resolution": "The bell stayed quiet until the proper watch, and the crew wrote down the repair.",
        "joke": "Patch kept the bucket helmet because it made every order sound important.",
        "ending": "One true evening bell rang while Pip cooed from the peaceful mast.",
    },
    {
        "title": "the sailmaker's measure",
        "premise": "A new patch for the mainsail came out shorter than the sailmaker expected.",
        "mistake": "Patch decided a spider had nibbled the cloth because a web crossed the measuring table.",
        "coo": "Pip's coo seemed to agree, until the bird tapped the rolled measuring cord.",
        "failed": "They measured with Patch's boot, but every step made the answer wobblier.",
        "clue": "a blue knot marking the unused remainder of the measuring cord",
        "cause": "the cord had been read from the wrong end after part of it stayed rolled",
        "action": "Mira unrolled the full cord, aligned its zero knot, and had Patch check the number",
        "resolution": "They cut a correctly sized patch and moved the table so the web could remain.",
        "joke": "Patch's boot was officially certified as exactly one Patch-boot long.",
        "ending": "The mended sail curved overhead while the old web trembled safely nearby.",
    },
    {
        "title": "the echoing chart room",
        "premise": "A soft coo sounded from inside the locked chart room while Pip sat on deck.",
        "mistake": "Mira feared another bird had become trapped behind the door.",
        "coo": "Pip answered the sound, and every reply came back a little flatter.",
        "failed": "Patch called, 'State your pirate business!' and heard only a very polite coo.",
        "clue": "a speaking tube ending beside a dusty web in the chart room",
        "cause": "Pip's voice traveled down the tube and echoed from its metal cap",
        "action": "They opened the room normally, traced the tube together, and tested one quiet sound",
        "resolution": "They labeled the tube and stopped worrying; the remainder of their watch stayed calm.",
        "joke": "Patch asked the echo for advice, and it wisely repeated only the last word.",
        "ending": "Moonlight circled the tube, the web, and three relieved smiles.",
    },
    {
        "title": "the missing invitation",
        "premise": "Only half of an island festival invitation could be found in the message box.",
        "mistake": "Patch assumed the phrase 'bring the remainder' meant the islanders wanted leftover stew.",
        "coo": "Pip cooed beside the message box whenever the lid rattled.",
        "failed": "Patch packed a cold potato and called it diplomatic stew.",
        "clue": "matching torn paper caught against a web under the lid",
        "cause": "a gust had torn the invitation, leaving the remainder tucked beneath the hinge",
        "action": "Mira held the lid steady while Patch lifted the paper with a smooth card",
        "resolution": "The joined invitation asked them to bring the remainder of their music rehearsal, so they practiced a song.",
        "joke": "The cold potato attended anyway and sat in the front row.",
        "ending": "Their finished song floated over lanterns while the mended invitation rested flat.",
    },
    {
        "title": "the water-barrel mark",
        "premise": "The drinking-water gauge showed less water than the morning tally promised.",
        "mistake": "Mira thought Pip's worried coo meant a leak was hiding behind the barrels.",
        "coo": "Pip stared at a web across the old gauge rather than at the dry deck.",
        "failed": "Patch listened to every barrel and claimed one sounded slightly seasick.",
        "clue": "a clean gauge line visible through a gap in the dusty web",
        "cause": "the web made an old scratch look like the current water mark",
        "action": "They checked for dampness, measured the barrels directly, and marked the true level without touching the web",
        "resolution": "Nothing had leaked; they corrected the tally and added a clear gauge cover.",
        "joke": "The seasick barrel recovered the moment Patch stopped singing to it.",
        "ending": "Fresh water cups caught the sunrise beneath the new clear marker.",
    },
    {
        "title": "the compass-card remainder",
        "premise": "A paper compass lesson had been cut into eight direction cards, but only seven lay on the table.",
        "mistake": "Patch followed Pip's coo north and nearly searched the mop closet for the remainder.",
        "coo": "Pip was facing north only because a warm sunbeam reached the rigging there.",
        "failed": "The mop was questioned and remained stubbornly directionless.",
        "clue": "the corner of the west card visible behind a web-framed chart",
        "cause": "the card had slid behind the chart when the table tilted",
        "action": "Mira compared the seven labels, identified west as missing, and asked Patch to lift the chart carefully",
        "resolution": "They recovered the west card and completed the compass lesson without disturbing the web.",
        "joke": "Patch promoted the mop to Admiral of Nowhere in Particular.",
        "ending": "Eight direction cards formed a bright compass rose on the steady table.",
    },
    {
        "title": "the cargo-label mix-up",
        "premise": "Two crates arrived marked COCOA and COCO, and the cargo list showed one crate remaining.",
        "mistake": "Mira heard Pip coo and thought the list was calling for the bird instead of cocoa.",
        "coo": "Pip cooed louder each time Patch read COCO aloud.",
        "failed": "Patch offered the bird a tiny customs form, which Pip promptly sat on.",
        "clue": "a missing letter A printed on a label corner caught in a web",
        "cause": "the cocoa label had torn, making its word look like the bird's sound",
        "action": "They matched weights and seals, restored the label, and checked the remainder against the full list",
        "resolution": "The final crate was cocoa for the galley; Pip was a passenger and owed no paperwork.",
        "joke": "Pip signed the rejected form with one magnificent feather mark.",
        "ending": "Warm cocoa steamed in mugs beside the neatly corrected cargo list.",
    },
    {
        "title": "the moonlit fishing line",
        "premise": "A bright strand stretched across the stern, and the crew feared a fishing line had snagged the ship.",
        "mistake": "Patch counted Pip's coos as tugs from an enormous invisible fish.",
        "coo": "Pip was greeting the moon, not reporting anything beneath the water.",
        "failed": "Patch introduced himself to the supposed fish and offered it command of the night watch.",
        "clue": "dew drops forming a perfect wheel on the bright strand",
        "cause": "moonlight was shining through a harmless spider web between two unused rails",
        "action": "Mira checked from a safe distance, compared the strand with real line, and rerouted foot traffic",
        "resolution": "They left the web alone and finished the remainder of the watch without a snag.",
        "joke": "The invisible fish never reported for duty, which Patch called poor manners.",
        "ending": "The moon turned every drop on the web into a tiny silver lantern.",
    },
    {
        "title": "the mapmaker's subtraction",
        "premise": "A mapmaker sent twelve island stamps and asked the crew to use nine, then record the remainder.",
        "mistake": "Mira thought a coo from the shelf meant Pip had hidden the unused stamps.",
        "coo": "Pip was calling to its reflection in a brass compass below a web.",
        "failed": "Patch searched his hat and discovered only yesterday's sandwich receipt.",
        "clue": "three square outlines beneath a transparent map weight",
        "cause": "the three remaining stamps were under the weight where Mira had placed them for safety",
        "action": "They reconstructed each step, subtracted nine from twelve, and lifted the weight together",
        "resolution": "The record correctly showed a remainder of three, and Pip was cleared of all stamp-related charges.",
        "joke": "Patch filed the sandwich receipt under Very Important Crumbs.",
        "ending": "Three unused stamps rested in an envelope below the gleaming compass.",
    },
)


OPENINGS = (
    "The puzzle began before the morning bell.",
    "Patch later swore the sea itself had arranged the joke.",
    "On a calm blue watch, one small mismatch stopped the crew.",
    "The Wobblefin had weathered storms, but that day it faced a quieter mystery.",
    "Mira first noticed trouble when Patch counted aloud and then counted again.",
    "Pip's coo reached the deck just as an ordinary task became puzzling.",
    "A shipboard record, a silver web, and one wrong guess began the adventure.",
    "Nobody expected the remainder to cause so much commotion.",
    "The crew's funniest investigation started with careful work and a sudden coo.",
    "Near noon, the Wobblefin carried a mystery too small for a cannon and too odd to ignore.",
)


def _sentence_start(text: str) -> str:
    return text[:1].upper() + text[1:]


def _ground_text(text: str, hero: Entity, mate: Entity, bird: Entity) -> str:
    replacements = (("Mira", hero.id), ("Patch", mate.id), ("Pip", bird.id))
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _ground_case(case: dict[str, str], hero: Entity, mate: Entity, bird: Entity) -> dict[str, str]:
    grounded: dict[str, str] = {}
    for key, value in case.items():
        grounded[key] = _ground_text(value, hero, mate, bird)
    return grounded


def _tell_case(world: World, hero: Entity, mate: Entity, bird: Entity, case: dict[str, str], route: int) -> None:
    hero.memes["curiosity"] = 1
    mate.memes["confusion"] = 1
    bird.memes["play"] = 1
    world.say(_ground_text(OPENINGS[route % len(OPENINGS)], hero, mate, bird))
    world.say(
        f"Aboard {world.ship.name}, {hero.id} the young {hero.type}, {mate.id} the {mate.type}, "
        f"and {bird.id} the {bird.type} faced {case['title']}."
    )
    world.say(case["premise"])
    world.para()

    if route % 3 == 0:
        world.say(case["coo"])
        world.say(f"'Then we should test what we think we heard,' {hero.id} said. {case['mistake']}")
    elif route % 3 == 1:
        world.say(case["mistake"])
        world.say(f"'A coo is a sound, not proof,' {hero.id} replied. {case['coo']}")
    else:
        world.say(f"'Before we decide, what do we actually know?' asked {hero.id}. {case['coo']}")
        world.say(case["mistake"])
    world.say(case["failed"])
    world.say(f"Instead of guessing again, they looked for evidence and found {case['clue']}.")
    world.para()

    world.say(f"That clue changed the story: {case['cause']}.")
    world.say(f"{_sentence_start(case['action'])}.")
    world.say(case["resolution"])
    world.say(f"'So the coo made us curious, but the clue made us certain,' said {mate.id}. {case['joke']}")
    world.para()
    world.say(
        "They learned that a misunderstanding grows when people defend a guess, "
        "and shrinks when friends compare evidence and listen to one another."
    )
    world.say(case["ending"])

    hero.memes["joy"] = 1
    mate.memes["confusion"] = 0
    mate.memes["joy"] = 1
    world.facts.update(
        scenario_title=case["title"],
        premise=case["premise"],
        misunderstanding=case["mistake"],
        coo_event=case["coo"],
        clue=case["clue"],
        cause=case["cause"],
        action=case["action"],
        resolution=case["resolution"],
        ending=case["ending"],
        coo_source=bird.id,
        web_found=True,
        remainder_found=True,
        resolved=True,
    )


def tell(params: StoryParams) -> World:
    world = World(Ship())
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    mate = world.add(Entity(id=params.mate_name, kind="character", type=params.mate_type))
    bird = world.add(Entity(id=params.bird_name, kind="character", type=params.bird_type))
    world.facts.update(hero=hero, mate=mate, bird=bird)

    case = _ground_case(SCENARIOS[params.scenario % len(SCENARIOS)], hero, mate, bird)
    _tell_case(world, hero, mate, bird, case, params.route)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    bird = world.facts["bird"]
    return [
        f"Write a short pirate tale for a small child about {hero.id}, {mate.id}, and {bird.id} solving {world.facts['scenario_title']}.",
        f"Tell a funny shipboard misunderstanding involving a coo, a web, and a remainder; the decisive clue is {world.facts['clue']}.",
        f"Write a gentle pirate adventure where friends test a mistaken guess, discover that {world.facts['cause']}, and repair the problem together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    mate = world.facts["mate"]
    bird = world.facts["bird"]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id}, the little {hero.type}, sailing with {mate.id} and {bird.id}.",
        ),
        QAItem(
            question=f"What did {bird.id}'s coo make the crew misunderstand?",
            answer=f"{world.facts['misunderstanding']} The coo drew their attention, but it did not prove their guess.",
        ),
        QAItem(
            question=f"What evidence helped solve {world.facts['scenario_title']}?",
            answer=f"They found {world.facts['clue']}. That evidence gave them something stronger than a guess.",
        ),
        QAItem(
            question="What was the real cause of the problem?",
            answer=f"The real cause was that {world.facts['cause']}. Once the friends understood that, they could act safely.",
        ),
        QAItem(
            question=f"How did {hero.id} and {mate.id} resolve the misunderstanding?",
            answer=f"{_sentence_start(world.facts['action'])}. {world.facts['resolution']}",
        ),
        QAItem(
            question="What did the friends learn from the mix-up?",
            answer="They learned to compare evidence and listen to one another before defending a guess. That turned the misunderstanding into a solution.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a web?",
            answer="A web is sticky silk made by a spider, and it can catch small things that drift into it.",
        ),
        QAItem(
            question="What does coo mean?",
            answer="A coo is a soft, gentle bird sound.",
        ),
        QAItem(
            question="What is a remainder?",
            answer="A remainder is what is left over after the rest is gone or already used.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: type={ent.type} meters={meters} memes={memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("setting", "ship"))
    lines.append(asp.fact("feature", "humor"))
    lines.append(asp.fact("feature", "misunderstanding"))
    lines.append(asp.fact("word", "coo"))
    lines.append(asp.fact("word", "web"))
    lines.append(asp.fact("word", "remainder"))
    lines.append(asp.fact("can_sound", "bird", "coo"))
    lines.append(asp.fact("can_hold", "web", "remainder"))
    lines.append(asp.fact("can_cause", "misunderstanding", "coo"))
    return "\n".join(lines)


ASP_RULES = r"""
shown(humor) :- feature(humor).
shown(misunderstanding) :- feature(misunderstanding).
shown(tale) :- word(coo), word(web), word(remainder).
shown(revealed_remainder) :- can_hold(web, remainder), can_cause(misunderstanding, coo).
#show shown/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_model_atoms() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show shown/1."))
    return sorted(set(asp.atoms(model, "shown")))


def asp_verify() -> int:
    expected = {("humor",), ("misunderstanding",), ("tale",), ("revealed_remainder",)}
    got = set(asp_model_atoms())
    if got == expected:
        print(f"OK: ASP parity verified ({len(got)} atoms).")
        return 0
    print("MISMATCH:")
    print("got:", sorted(got))
    print("expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a coo, a web, and a remainder.")
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--bird")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(
    args: argparse.Namespace, rng: random.Random, sample_seed: Optional[int] = None
) -> StoryParams:
    seed = sample_seed if sample_seed is not None else args.seed
    if seed is None:
        seed = rng.randrange(2**31)
    return StoryParams(
        seed=seed,
        name=args.name or rng.choice(["Mira", "Nell", "Jory", "Rae", "Finn"]),
        hero_type="captain",
        mate_name=args.mate or rng.choice(["Patch", "Moss", "Brine", "Wren"]),
        mate_type="pirate",
        bird_name=args.bird or rng.choice(["Pip", "Coco", "Skim", "Twee"]),
        bird_type="seabird",
        scenario=seed % len(SCENARIOS),
        route=(seed // len(SCENARIOS)) % len(OPENINGS),
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
        print(asp_program("#show shown/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{x[0]}" for x in asp_model_atoms()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        seeds = [base_seed + i for i in range(5)]
    else:
        seeds = [base_seed + i for i in range(args.n)]

    seen: set[str] = set()
    for i, seed in enumerate(seeds):
        rng = random.Random(seed)
        params = resolve_params(args, rng, seed)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
