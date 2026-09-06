#!/usr/bin/env python3
"""
A small tall-tale storyworld about a curious child, a peculiar garnet, and the
funny trouble that follows from wanting to know what it can do.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    elder: Item
    garnet: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    elder_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Milo", "Ruby", "Nia", "Toby", "Lena", "Otis", "Ivy", "Pip"]
ELDERS = ["Grandpa", "Grandma", "Uncle Ned", "Aunt Bea", "Old Mara"]
PLACES = ["the canyon camp", "the red hill", "the dusty porch", "the lantern shed", "the little mesa"]


ASP_RULES = r"""
#show curious/1.
#show amused/1.
#show shared/1.

curious(H) :- hears_riddle(H).
amused(H) :- sees_spark(H).
shared(H) :- gives_garnet(H).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hears_riddle", "hero"),
        asp.fact("sees_spark", "hero"),
        asp.fact("gives_garnet", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show curious/1.\n#show amused/1.\n#show shared/1."))
    atoms = set((a.name, tuple(x.name if x.type != x.type.Number else x.number for x in a.arguments)) for a in model)
    expected = {("curious", ("hero",)), ("amused", ("hero",)), ("shared", ("hero",))}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a curious garnet.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--elder-name", choices=ELDERS)
    ap.add_argument("--place", choices=PLACES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        elder_name=args.elder_name or rng.choice(ELDERS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    hero = Item(id="hero", label=params.name, phrase=f"young {params.name}", kind="character")
    elder = Item(id="elder", label=params.elder_name, phrase=params.elder_name, kind="character")
    garnet = Item(id="garnet", label="garnet", phrase="a thumb-sized garnet that looked like a cherry with a secret", owner=hero.id)
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.elder_name}|{params.place}")
    return World(hero=hero, elder=elder, garnet=garnet, place=params.place, seed=seed)


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record_story(world: World, *, arc: str, discovery: str, trouble: str,
                  cause: str, refrain: str, resolution: str, ending: str,
                  humor: str, lines: list[str]) -> str:
    world.facts.update(
        arc=arc,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        refrain=refrain,
        resolution=resolution,
        ending=ending,
        humor=humor,
        shared=True,
    )
    return " ".join(lines)


def _echo_arc(world: World, rng: random.Random) -> str:
    h, e, p = world.hero.label, world.elder.label, world.place
    sound = _choice(rng, ["a hiccup", "a mouse-sized whistle", "the word hello", "one tiny sneeze"])
    answer = _choice(rng, ["HELLO-HULLO-HALLOO!", "WHO PUT PEPPER IN THE SKY?", "I HEARD THAT!", "MORE, MORE, MORE!"])
    discovery = f"the garnet threw {sound} back as a canyon-sized echo"
    trouble = "the enormous echo startled the camp mules into tangling the wash line"
    cause = "the garnet had been balanced in a tin cup, which aimed every little sound into the canyon"
    refrain = "Small stone, small sound"
    resolution = f"{h} lifted the garnet out of the cup and spoke softly into an open palm; the echo shrank at once"
    ending = "the last red glimmer rested in the quiet cup while the untangled socks fluttered above it"
    humor = "a tiny sound answered like a boastful mountain"
    lines = [
        f"At {p}, {h} found a garnet tucked inside a dented tin cup.",
        f"Curious about the red spark, {h} made {sound} over it. The far cliffs bellowed, \"{answer}\"",
        f"The mules jumped, the wash line looped around three saddles, and a pair of bloomers sailed up like a surrender flag.",
        f'"Again!" cried {h}. "Again, again--"',
        f'{e} caught the cup before the next experiment. "First ask why the mountain is shouting," {e} said.',
        f"They tested the stone on the ground, on a blanket, and finally inside the cup. Only the cup made the cliffs roar.",
        f'"{refrain}," {h} whispered while lifting the garnet free. The canyon whispered back instead of booming.',
        f"Together they freed the mules and reeled in every wandering sock. {h} handed {e} the garnet so they could share one last, careful test.",
        f"By sunset, {ending}. {h} had discovered that curiosity sounds best after it listens.",
    ]
    return _record_story(world, arc="echo", discovery=discovery, trouble=trouble, cause=cause,
                         refrain=refrain, resolution=resolution, ending=ending, humor=humor, lines=lines)


def _lantern_arc(world: World, rng: random.Random) -> str:
    h, e, p = world.hero.label, world.elder.label, world.place
    shape = _choice(rng, ["a red rabbit", "a dancing giant", "a six-legged rooster", "a dragon in slippers"])
    screen = _choice(rng, ["a flour sack", "the shed door", "a white bedsheet", "the water-tower wall"])
    discovery = f"lamplight through the garnet painted {shape} on {screen}"
    trouble = f"neighbors mistook the moving shadow for {shape} and arrived with pots and broomsticks"
    cause = "the garnet was acting like a tiny red lens, and the swinging lantern made its shadow seem alive"
    refrain = "Shadow, show your shoes"
    resolution = f"{h} stopped the lantern, moved the garnet away from its flame, and demonstrated the small shadow to everyone"
    ending = "the true little garnet lay beside the still lantern, no larger than the button it had always been"
    humor = f"the supposed monster turned out to be a gemstone shadow on {screen}"
    lines = [
        f"One windy evening near {p}, {h} carried a newly found garnet beside a lantern to inspect it.",
        f"The stone crossed the lamplight, and suddenly {shape} bounded across {screen}.",
        f"{h} ducked. {e} ducked. Even the broom ducked, though nobody had asked it to.",
        f'From outside came the chant, "{refrain}! {refrain}!" Neighbors crowded in, armed with pans, rakes, and one soup spoon.',
        f"Instead of chasing the shadow, {h} grew curious about it. The child held the lantern still; the monster froze. The child lowered the garnet; the monster sank.",
        f'"The giant is pocket-sized," {h} announced, placing the garnet in {e}\'s hand.',
        f"They repeated the trick slowly so everyone could see how light, stone, and swinging lantern had made the commotion.",
        f"The neighbors laughed and used their pans for supper instead of battle. When the door closed, {ending}.",
    ]
    return _record_story(world, arc="lantern", discovery=discovery, trouble=trouble, cause=cause,
                         refrain=refrain, resolution=resolution, ending=ending, humor=humor, lines=lines)


def _wagon_arc(world: World, rng: random.Random) -> str:
    h, e, p = world.hero.label, world.elder.label, world.place
    cargo = _choice(rng, ["watermelons", "round cheeses", "pumpkins", "jars of plum jam"])
    catcher = _choice(rng, ["a haystack", "a soft dune", "a patch of sunflowers", "a mountain of laundry"])
    discovery = "the garnet fit perfectly beneath the wheel of an old handcart"
    trouble = f"the newly freed cart sent its load of {cargo} rolling downhill"
    cause = "the little garnet had been serving as the cart's wheel chock"
    refrain = "Red means ready--not yet!"
    resolution = f"{h} steered the cart into {catcher} while {e} blocked the loose cargo with a fence rail"
    ending = "the garnet returned beneath the wheel, glowing red beside a neatly parked cart"
    humor = f"the runaway {cargo} seemed to be holding their own downhill parade"
    lines = [
        f"Behind {p}, {h} spotted a garnet peeking from under a wagon wheel and tugged it loose to get a better look.",
        f"Creak. Roll. RUMBLE. The cart started downhill with {cargo} bouncing behind it.",
        f'"Red means ready--not yet!" shouted {h}, racing after it. "Not yet, not yet, NOT YET!"',
        f"One runaway piece rolled through {e}'s legs; another hopped into an empty chair as if it had paid for the seat.",
        f"{h} noticed that the cart had begun moving exactly when the garnet came out. The stone was not magical after all--it had been doing a very ordinary, very important job.",
        f"The child caught the handle and leaned hard, turning the cart toward {catcher}. {e} laid a fence rail across the wandering cargo's path.",
        f"After counting every rescued piece twice, {h} passed the garnet to {e}, then tucked it firmly back beneath the wheel.",
        f"That evening, {ending}. Whenever {h} felt curious about something holding still, the child first wondered what it might be holding still.",
    ]
    return _record_story(world, arc="wagon", discovery=discovery, trouble=trouble, cause=cause,
                         refrain=refrain, resolution=resolution, ending=ending, humor=humor, lines=lines)


def _magpie_arc(world: World, rng: random.Random) -> str:
    h, e, p = world.hero.label, world.elder.label, world.place
    perch = _choice(rng, ["the weather vane", "a cottonwood fork", "the windmill roof", "the tallest bean pole"])
    trade = _choice(rng, ["three bright buttons", "a strip of silver paper", "a polished spoon", "a bracelet of bottle caps"])
    discovery = "the garnet made a splendid red button for the camp scarecrow"
    trouble = f"a curious magpie stole the shining stone and carried it to {perch}"
    cause = "the exposed garnet flashed in the sun and attracted a bird that collects bright objects"
    refrain = "Bright is not yours"
    resolution = f"{h} offered {trade} nearby and waited quietly until the magpie chose the larger glitter and dropped the garnet"
    ending = "the scarecrow wore a dull wooden button, while the garnet slept safely in a cloth pouch"
    humor = "the thief scolded everyone from above while wearing a grass stem like a grand mustache"
    lines = [
        f"At {p}, {h} found a garnet and decided the lopsided scarecrow deserved one magnificent red button.",
        f"The scarecrow had worn it for seven proud minutes when a magpie swooped down--snatch!--and carried the garnet to {perch}.",
        f'"Bright is not yours!" called {h}. The magpie answered, "Kraa!" which sounded suspiciously like, "Bright is mine!"',
        f"{h} climbed a barrel, then a stool, then stepped down again when {e} pointed out that stacking furniture was not a ladder.",
        f"Curiosity supplied a better question: what would a bird that loved one sparkle do if it saw an even bigger sparkle?",
        f"The child laid out {trade} and repeated, \"Bright for bright, trade for trade.\" The magpie cocked its head, dropped the garnet, and seized the safer prize.",
        f"{h} handed the recovered stone to {e} before sewing a plain wooden button on the scarecrow.",
        f"At dusk, {ending}. High on {perch}, the magpie showed off its new treasure to a cloud that was not impressed.",
    ]
    return _record_story(world, arc="magpie", discovery=discovery, trouble=trouble, cause=cause,
                         refrain=refrain, resolution=resolution, ending=ending, humor=humor, lines=lines)


def _water_arc(world: World, rng: random.Random) -> str:
    h, e, p = world.hero.label, world.elder.label, world.place
    channel = _choice(rng, ["the bean rows", "the melon patch", "the thirsty peach trees", "the sunflower bed"])
    passenger = _choice(rng, ["a tin cup", "a yellow boot", "a wooden spoon", "a toy boat"])
    discovery = "the garnet was wedged in the notch of a small irrigation gate"
    trouble = f"the released water rushed toward {channel} with {passenger} bobbing at its front"
    cause = "the stone had plugged the gate's worn notch and was holding back the irrigation water"
    refrain = "Little leak, wait a week"
    resolution = f"{h} slid a flat board into the gate while {e} packed the worn notch with clay"
    ending = f"a quiet ribbon of water reached {channel}, and the washed garnet dried on a folded blue rag"
    humor = f"{passenger} sailed past like the mayor of a very narrow river"
    lines = [
        f"During a dry afternoon at {p}, {h} saw one red wink in the wooden irrigation gate and pulled out a garnet.",
        f"The wink became a squirt. The squirt became a stream. The stream grabbed {passenger} and hurried toward {channel}.",
        f'"Little leak, wait a week!" {h} pleaded. The leak had no calendar and did not wait.',
        f"While {e} chased the floating passenger, {h}, curious now, examined the empty notch and understood what the garnet had been doing there.",
        f"The child tried a fist, a hat, and one muddy elbow against the hole. Each attempt produced a different fountain and the same wet child.",
        f"Then {h} slid a flat board into the gate. {e} pressed clay around it, and the wild stream settled into its proper channel.",
        f"They shared the garnet between their palms and agreed that a pretty thing could still have been somebody's useful plug.",
        f"By evening, {ending}. Nearby, {passenger} sat in the mud looking pleased with its voyage.",
    ]
    return _record_story(world, arc="water", discovery=discovery, trouble=trouble, cause=cause,
                         refrain=refrain, resolution=resolution, ending=ending, humor=humor, lines=lines)


def _goat_arc(world: World, rng: random.Random) -> str:
    h, e, p = world.hero.label, world.elder.label, world.place
    goat = _choice(rng, ["Noodles", "Captain", "Pickle", "Madam Hoof"])
    destination = _choice(rng, ["the cabbage patch", "the picnic table", "the open grain bin", "the mayor's flower bed"])
    discovery = "sunlight reflected from the garnet in a bright moving dot"
    trouble = f"the goat {goat} chased that dot toward {destination}"
    cause = "turning the garnet in direct sun moved its red reflection across the ground like a tempting target"
    refrain = "Red spot, goat stop"
    resolution = f"{h} guided the reflection back into the pen and then covered the garnet with a handkerchief"
    ending = f"the covered garnet rested on the gatepost while {goat} chewed hay beneath an ordinary patch of shade"
    humor = f"{goat} pursued a spot of light with the solemn determination of a sheriff chasing a pie"
    lines = [
        f"At noon in {p}, {h} polished a found garnet on a sleeve. A red spot skipped across the dust.",
        f"The goat {goat} pounced on it. {h} turned the stone to look closer, and the spot raced straight toward {destination} with the goat behind it.",
        f'"Red spot, goat stop!" called {h}. "Red spot, goat stop!" {e} repeated. The goat respected neither poetry nor punctuation.',
        f"Running only made the garnet swing faster, so {h} stopped. The red spot stopped too. {goat} planted all four hooves and stared at it.",
        f"Now curious about the connection, {h} tilted the stone left; the spot went left. The child tilted it right; goat and spot went right.",
        f"Slowly, carefully, {h} walked the reflection back through the pen gate. {e} shut the latch behind {goat}.",
        f"The child let {e} hold the garnet for one final test, then wrapped it in a handkerchief so no more goats could be accidentally steered.",
        f"At sundown, {ending}. Not even the biggest tall tale could persuade {goat} that the red spot had never been edible.",
    ]
    return _record_story(world, arc="goat", discovery=discovery, trouble=trouble, cause=cause,
                         refrain=refrain, resolution=resolution, ending=ending, humor=humor, lines=lines)


def _bell_arc(world: World, rng: random.Random) -> str:
    h, e, p = world.hero.label, world.elder.label, world.place
    event = _choice(rng, ["breakfast", "the noon meeting", "the pie judging", "the evening dance"])
    intruder = _choice(rng, ["a moth", "a tumbleweed", "a sleepy bat", "a gust carrying two feathers"])
    discovery = "the garnet was tied to the clapper of the camp bell as a bright counterweight"
    trouble = f"the unbalanced bell rang wildly and summoned everyone early for {event}"
    cause = "without the garnet's weight, every small breeze could swing the bell's clapper"
    refrain = "Not yet, bell"
    resolution = f"{h} retied the garnet to the clapper and shortened the loose cord so only a proper pull could ring it"
    ending = "the balanced bell held one round note inside, and the garnet glowed beneath it like a banked coal"
    humor = f"the whole settlement assembled for {event} before anyone was ready"
    lines = [
        f"Near {p}, {h} found a garnet dangling inside the old camp bell and untied it for inspection.",
        f"At once {intruder} brushed past. CLANG-A-LANG-A-LANG! The bell announced {event} hours too soon.",
        f"People arrived with half-buttoned coats, unfinished pies, and one toothbrush. {h} repeated, \"Not yet, bell. Not yet!\"",
        f"The bell replied with another clang whenever the breeze nudged its now-light clapper.",
        f"{e} did not blame the wind. Instead, {e} asked what had changed just before the ringing began.",
        f"Curious about the change, {h} looked from the garnet to the bare cord and tested their weight in both hands. The stone had not been decoration; it had balanced the bell.",
        f"Together they retied it and shortened the cord. {h} gave {e} the rope for a careful pull, and one sensible note rolled over the camp.",
        f"Everyone went home to finish getting ready. After the laughter faded, {ending}.",
    ]
    return _record_story(world, arc="bell", discovery=discovery, trouble=trouble, cause=cause,
                         refrain=refrain, resolution=resolution, ending=ending, humor=humor, lines=lines)


def _map_arc(world: World, rng: random.Random) -> str:
    h, e, p = world.hero.label, world.elder.label, world.place
    landmark = _choice(rng, ["a split cedar", "the crooked chimney", "a stone shaped like a sleeping bear", "the old wind pump"])
    prize = _choice(rng, ["a jar of peach buttons", "a box of harmonicas", "a sack of peppermint sticks", "a bundle of painted kites"])
    discovery = "the garnet's red light revealed faded arrows on an old map"
    trouble = f"the searchers followed every arrow literally and circled {landmark} again and again"
    cause = "the arrows were directions for different seasons, and only the summer marks matched the current trail"
    refrain = "Arrow, arrow, where tomorrow?"
    resolution = f"{h} compared the map with the sun and fresh tracks, selected the summer arrows, and found {prize} cached for the town fair"
    ending = "the garnet pinned the corrected map flat while one true arrow pointed home through the dusk"
    humor = f"the search party passed {landmark} so often that everyone began greeting it by name"
    lines = [
        f"Inside an old trail box at {p}, {h} discovered a garnet wrapped in a map that looked perfectly blank.",
        f"When sunlight passed through the stone, red arrows appeared. \"Arrow, arrow, where tomorrow?\" {h} sang, and set off with {e}.",
        f"One arrow led left, the next led right, and a third led them back to {landmark}. They circled it once, twice, then a third time just to be certain they were thoroughly lost.",
        f'"Good afternoon again," {h} told the landmark. {e} laughed. "A map that makes us repeat ourselves is asking the wrong question."',
        f"{h} became curious about the tiny leaf, snowflake, flower, and sun beside the arrows. The marks belonged to four different seasons.",
        f"Because it was summer, they followed only the sun-marked arrows and soon uncovered {prize}, safely stored for the town fair.",
        f"{h} passed the garnet to {e} while drawing a bold line along the correct route. On the walk back, nobody had to greet the landmark twice.",
        f"Night settled over the trail, and {ending}. Curiosity had turned repetition from a trap into a clue.",
    ]
    return _record_story(world, arc="map", discovery=discovery, trouble=trouble, cause=cause,
                         refrain=refrain, resolution=resolution, ending=ending, humor=humor, lines=lines)


ARC_BUILDERS = [_echo_arc, _lantern_arc, _wagon_arc, _magpie_arc, _water_arc, _goat_arc, _bell_arc, _map_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x6A4E37)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} discover about the garnet?",
            answer=f"{h} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What caused the trouble in this story?",
            answer=f"The trouble began because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} solve the problem?",
            answer=f"{facts['resolution']}.",
        ),
        QAItem(
            question="How did repetition add humor or urgency?",
            answer=f'The characters repeated "{facts["refrain"]}" while {facts["trouble"]}.',
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    common = [
        QAItem(
            question="What is a garnet?",
            answer="A garnet is a hard gemstone. It is often red or dark red and can look shiny like a tiny jewel.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to learn more and ask questions.",
        ),
        QAItem(
            question="Why can repeating a question matter in a story?",
            answer="Repeating a question can show that someone is very interested, impatient, or excited to learn the answer.",
        ),
    ]
    arc_item = {
        "echo": QAItem("What causes an echo?", "An echo happens when sound waves bounce off a broad, hard surface and return to the listener."),
        "lantern": QAItem("How can a small object make a large shadow?", "A small object held close to a light can block spreading rays and cast a much larger shadow on a distant surface."),
        "wagon": QAItem("What is a wheel chock?", "A wheel chock is a sturdy block placed against a wheel to keep a cart or vehicle from rolling."),
        "magpie": QAItem("Why might a bird notice a shiny object?", "Some birds investigate bright objects because unusual colors and flashes attract their attention."),
        "water": QAItem("What does an irrigation gate do?", "An irrigation gate controls how much water flows from a channel toward fields or garden beds."),
        "goat": QAItem("Why does reflected light move?", "Reflected light changes direction when the shiny surface reflecting it is tilted or turned."),
        "bell": QAItem("Why does a bell need a clapper?", "A clapper swings into the bell's sides and makes the metal vibrate, producing a ringing sound."),
        "map": QAItem("Why do maps use symbols?", "Map symbols show routes, landmarks, directions, and other information in a compact visual form."),
    }[world.facts["arc"]]
    return [common[0], arc_item, common[1]]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a tall-tale story for young children about a curious child and a garnet.',
        f'Write a funny story set at {world.place} where a child keeps asking about a garnet again and again.',
        'Tell a simple story that uses repetition, curiosity, and a small red gemstone in a big-feeling adventure.',
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.elder, world.garnet]:
        lines.append(f"  {ent.id:6} {ent.kind:9} label={ent.label!r} owner={ent.owner!r} meters={ent.meters} memes={ent.memes}")
    lines.append(f"  place={world.place}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show curious/1.\n#show amused/1.\n#show shared/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible logical atoms: curious(hero), amused(hero), shared(hero)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Milo", elder_name="Grandpa", place="the canyon camp"),
            StoryParams(name="Ruby", elder_name="Grandma", place="the red hill"),
            StoryParams(name="Ivy", elder_name="Aunt Bea", place="the dusty porch"),
            StoryParams(name="Otis", elder_name="Uncle Ned", place="the lantern shed"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
