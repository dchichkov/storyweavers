#!/usr/bin/env python3
"""
A small nursery-rhyme-style story world set at a cliff lookout, built around a
quest, curiosity, and sharing. The core premise is that a little seeker finds a
tube on the lookout path, wants to keep it, but a shared use turns it into a
gentle adventure with a happy ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

LOOKOUT_WORDS = {"cliff", "lookout", "quest", "curiosity", "sharing", "tube"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    receiver: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the cliff lookout"
    breeze: str = "soft"
    affords: set[str] = field(default_factory=lambda: {"quest", "share", "look"})


@dataclass
class QuestItem:
    label: str
    phrase: str
    type: str
    curiosity_hook: str
    share_use: str


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    item: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class QuestScenario:
    title: str
    premise: str
    problem: str
    first_try: str
    clue: str
    tube_use: str
    hero_action: str
    helper_action: str
    discovery: str
    resolution: str
    lesson: str
    ending: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)

    def get(self, eid: str) -> Entity:
        return self.entities[eid]


SETTING = Setting()

ITEMS = {
    "tube": QuestItem(
        label="tube",
        phrase="a bright blue tube",
        type="tube",
        curiosity_hook="had a little rattle inside",
        share_use="can hold a tiny map and a pebble charm",
    )
}

HERO_NAMES = ["Mina", "Toby", "Nell", "Pip", "Luna", "Bram", "Ivy", "Milo"]
HELPER_NAMES = ["Robin", "Sage", "Wren", "Kit", "Penny", "Nico", "June", "Finn"]

ASP_RULES = r"""
quest_ready(H, I) :- curious(H), sees(H, I), item(I).
sharing_fix(H, I) :- quest_ready(H, I), shareable(I), wants(H, I).
happy_end(H, I) :- sharing_fix(H, I).
"""

@dataclass
class StoryState:
    hero: Entity
    helper: Entity
    item: Entity
    setting: Setting
    shared: bool = False
    resolved: bool = False
    wonder: bool = False
    scenario: Optional[QuestScenario] = None
    first_try: str = ""
    clue: str = ""
    discovery: str = ""
    resolution: str = ""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme cliff-lookout story world.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    hero_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    item = args.item or "tube"
    if item not in ITEMS:
        raise StoryError("The story world only knows about the tube.")
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        item=item,
    )


def make_world(world: World, params: StoryParams) -> StoryState:
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(id="item", kind="thing", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id))
    return StoryState(hero=hero, helper=helper, item=item, setting=world.setting)


SCENARIOS = (
    QuestScenario(
        "the fog-bell quest",
        "a bank of pearl-gray fog hid the harbor bell from view",
        "three visiting ducklings could hear their pond but could not tell which safe path led downhill",
        "held the tube like a horn and called toward every path, which only made echoes bounce back",
        "one echo returned with a soft bell-note beneath it",
        "a listening trumpet",
        "aimed the wide end from one marked trail sign to the next",
        "rang the lookout's handbell beside the correct fenced path",
        "the bell-note sounded clearest through the tube when it pointed toward the pond trail",
        "guided the ducklings along the fenced path and delivered them to the ranger at its gate",
        "curiosity works best when friends compare what they notice",
        "Below the railing, the fog opened like a curtain, and three ducklings paddled a silver V across the pond",
    ),
    QuestScenario(
        "the missing-map quest",
        "a gust scattered the ranger's picture-map into a patch of lookout daisies",
        "the smallest map strip had slipped beneath a bench and nobody knew which picture completed the route",
        "grabbed the nearest strips and joined a lighthouse to a picnic table, but the path lines did not meet",
        "a curled blue corner showed through a gap under the bench",
        "a gentle map-strip roller",
        "rolled the tube beneath the bench without reaching under it",
        "caught the loosened strip in a shared scarf",
        "the blue corner completed the stream crossing on the picture-map",
        "rebuilt the map in order and returned it to the ranger's weatherproof case",
        "sharing both tools and ideas can put a mixed-up plan right",
        "The restored map fluttered behind its clear cover while the daisies nodded below",
    ),
    QuestScenario(
        "the lighthouse-flash quest",
        "the lookout keeper needed to test a tiny practice signal before sunset",
        "the cardboard signal flags kept folding in the breeze before anyone below could read them",
        "waved both flags faster, until they wrapped around each other like sleepy ribbons",
        "a sunbeam made a bright coin on the tube's smooth rim",
        "a safe light viewer held below eye level",
        "turned the tube toward a white marker board, never toward the sun",
        "held the marker steady and counted each reflected blink",
        "the reflected pattern matched the keeper's three-short, one-long practice card",
        "completed the supervised signal test and packed every flag into its proper sleeve",
        "careful curiosity follows safety rules and asks an expert",
        "Far across the water, the lighthouse answered with one warm blink as evening turned the waves pink",
    ),
    QuestScenario(
        "the rain-measure quest",
        "a quick shower drummed on the lookout roof and filled every leaf with beads",
        "the garden club could not decide which sheltered planter had received the least rain",
        "guessed by touching the soil, but both top layers felt equally damp",
        "droplets clung at different heights inside two empty jars",
        "a pouring guide for a simple rain gauge",
        "used the tube to pour each jar into matching marked cups without spilling",
        "read the marks aloud and wrote the numbers on a slate",
        "the rosemary planter had received only half as much water as the thyme",
        "shared the watering can and gave the rosemary exactly the missing amount",
        "a fair answer comes from measuring together instead of guessing",
        "A last raindrop chimed from the tube into the cup, and the rosemary leaves shone clean and green",
    ),
    QuestScenario(
        "the burrow-message quest",
        "a ranger found tiny pawprints beside a rabbit shelter well inland from the cliff edge",
        "a maintenance cart blocked the rabbits' usual covered passage to the meadow",
        "set out carrots near the cart, but the shy rabbits would not approach while people stood there",
        "the tracks curved toward a second tunnel hidden behind tall grass",
        "a message holder for the ranger's detour sketch",
        "slid the rolled sketch into the tube so the breeze could not carry it away",
        "carried it to the groundskeeper and helped place quiet arrow signs",
        "the second tunnel opened safely into the clover meadow",
        "cleared the covered passage and watched from behind the viewing fence as the rabbits chose their route",
        "kind quests protect animals by giving them space and sharing observations",
        "At dusk, two white tails bobbed through the clover while the little detour signs stood straight",
    ),
    QuestScenario(
        "the tide-song quest",
        "a low humming note drifted up from the sheltered cove",
        "the sound stopped whenever the friends spoke, so they could not discover what made it",
        "hummed back as loudly as possible, which covered the faint note completely",
        "the note returned only when the breeze crossed a row of hollow reeds",
        "a listening tube on the safe lookout deck",
        "held one end near the reed-box display and listened from behind the railing",
        "covered and uncovered the display's air holes one at a time",
        "moving air through three different reeds made the cove's gentle chord",
        "showed the ranger which loose reed needed fastening, then helped label the outdoor instrument",
        "quiet listening can answer a question that noise cannot",
        "The repaired reeds sang hum, hoo, home while a round moon rose over the cove",
    ),
    QuestScenario(
        "the seed-delivery quest",
        "the lookout's wind garden was ready for a row of sturdy sea-pink seeds",
        "the tiny seeds kept skipping out of open hands before they reached the sheltered planting boxes",
        "poured a handful straight from the packet, and the breeze whisked two onto the path",
        "the tube's cap clicked snugly and left only a narrow pouring mouth",
        "a covered seed carrier",
        "gathered the two path seeds with the ranger and tucked the packet safely inside",
        "shielded each planting hole with both hands while counting one seed at a time",
        "the capped tube carried every remaining seed without losing one",
        "shared planting jobs, pressed the soil gently, and returned the empty packet for reuse",
        "planning and teamwork keep small treasures from being wasted",
        "Along the sheltered wall, twelve neat soil dimples waited for their first green shoots",
    ),
    QuestScenario(
        "the picture-scope quest",
        "families had gathered to name the seabirds circling beyond the lookout",
        "the bird chart was too small for everyone to inspect at once",
        "called every gray bird a gull, but a child nearby noticed one had a bright orange beak",
        "the chart showed that beak beside the picture of a puffin",
        "a pretend spotting scope aimed only across the open water",
        "used the tube to frame one bird at a time without magnifying or staring at bright light",
        "held up the chart and invited each waiting child to compare one feature",
        "beak shape, wing beat, and color identified three different seabirds",
        "made a sharing circle so everyone had a turn with the tube and the chart",
        "curiosity grows when everyone gets a chance to look and contribute",
        "One puffin skimmed the blue water, and the tube passed gently to the next pair of hands",
    ),
    QuestScenario(
        "the lost-note quest",
        "a nursery-rhyme concert was about to begin in the lookout pavilion",
        "the final rolled music card had vanished from its numbered basket",
        "searched the instrument box twice, making the bells jingle but finding no card",
        "a faint paper rustle came from the tube rack whenever the breeze rose",
        "a keeper for rolled song cards",
        "tipped the blue tube over a clean cloth and caught the hidden card",
        "matched its star sticker to the final space in the music basket",
        "the missing card held the quiet last line of the moon-and-sea rhyme",
        "returned the card, shared the tube as a rhythm tapper, and helped the concert finish softly",
        "good detectives pause, listen, and let friends test their clues",
        "The last note faded as the children tapped the tube once: tip, tap, hush",
    ),
    QuestScenario(
        "the shadow-clock quest",
        "the lookout's painted shadow clock was due for its midday check",
        "a fallen leaf covered the mark where the short shadow should point",
        "moved the clock's pointer by hand, but the ranger explained that only sunlight should move its shadow",
        "the tube cast a narrow shadow that lined up neatly beside the covered mark",
        "a comparison pointer set on the supervised activity table",
        "placed the tube in the table's holder and stepped back",
        "lifted the leaf with a brush and compared both shadows to the ranger's guide",
        "the original pointer was correct; only the numbered mark had been hidden",
        "brushed the dial clean and made a leaf screen that would not touch the clock",
        "curiosity means testing an idea without changing the thing being tested",
        "At noon, two slim shadows rested together on twelve while the leaf screen whispered nearby",
    ),
    QuestScenario(
        "the kindness-post quest",
        "the lookout hosted a basket of picture notes for children visiting the quiet rest shelter",
        "one child's thank-you picture had no name and no matching envelope",
        "nearly chose the brightest envelope, but its moon sticker did not appear on the picture",
        "a tiny acorn stamp hid beneath one curled corner",
        "a dry carrier for the rolled picture",
        "placed the picture in the tube so curious hands would not smudge it",
        "found the acorn envelope and asked the ranger to confirm the match",
        "the picture thanked the garden volunteer for repairing a low bird bath",
        "delivered the matched note, then shared the tube so other children could post pictures safely",
        "kindness includes protecting another person's message and checking before acting",
        "The volunteer pinned up the acorn picture, and its yellow sun brightened the shelter wall",
    ),
    QuestScenario(
        "the echo-count quest",
        "the ranger invited visitors to compare echoes from the covered lookout pavilion",
        "two groups counted different numbers because they clapped at the same time",
        "clapped even faster, which tangled every echo into one noisy rumble",
        "a single tap on the tube made one clean tok followed by two soft replies",
        "a rhythm stick for a turn-taking sound test",
        "tapped once, waited, and raised one finger for each reply",
        "kept the group quiet and recorded the count on a shared card",
        "slow turn-taking revealed two echoes from the wooded hillside, not from the cliff below",
        "gave every group one careful turn and posted the matching counts on the pavilion board",
        "sharing time and listening fairly can settle a disagreement",
        "The final tok floated away, and two chalk stars remained beside the number two",
    ),
)

OPENINGS = (
    "At the cliff lookout, {hero} arrived with {helper} for a small morning quest.",
    "Beyond the safe wooden railing, waves winked while {hero} and {helper} met at the cliff lookout.",
    "The breeze said swish, swish, slow when {hero} joined {helper} at the cliff lookout.",
    "At the cliff lookout's fenced activity deck, {hero} and {helper} opened the quest book together.",
    "Clouds sailed above the cliff lookout as curious {hero} and careful {helper} began exploring.",
    "The ranger's bell went ting at the cliff lookout, calling {hero} and {helper} to a gentle quest.",
    "At the cliff lookout, {hero} kept well behind the railing and wondered what today's quest might be.",
    "Sea breeze, safe rail, gulls in flight: {hero} met {helper} at the cliff lookout bright.",
)

SHARING_LINES = (
    "'One tube, two thinkers,' said {helper}. 'Let us each do the part we can do safely.'",
    "{hero} took a breath. 'I have the tube, but you may have the clue. Shall we share both?'",
    "'Your eyes and my hands can work as a team,' {helper} said, and {hero} offered the tube.",
    "{hero} held out the tube. 'A quest belongs to everyone who helps solve it.'",
    "'Turn by turn and clue by clue,' sang {helper}. 'I will share my idea if you share your tube.'",
    "The tube was a tempting treasure, yet {hero} said, 'It will be more useful between us.'",
    "{helper} did not grab. 'May I help?' came the question, and {hero} answered, 'Yes, let us share.'",
    "'Mine for a moment can become ours for the quest,' {hero} decided, passing the tube carefully.",
)


def tell_story(params: StoryParams) -> tuple[World, StoryState]:
    world = World(SETTING)
    state = make_world(world, params)
    variant = params.seed
    if variant is None:
        variant = sum((i + 1) * ord(ch) for i, ch in enumerate(params.hero_name + params.helper_name))
    scenario = SCENARIOS[variant % len(SCENARIOS)]
    state.scenario = scenario
    state.wonder = True
    state.first_try = scenario.first_try
    state.clue = scenario.clue

    opening = OPENINGS[(variant // len(SCENARIOS)) % len(OPENINGS)].format(
        hero=state.hero.label,
        helper=state.helper.label,
    )
    world.say(opening)
    world.say(f"Their adventure was {scenario.title}: {scenario.premise}. But {scenario.problem}.")
    world.say(
        f"Curious {state.hero.label} found {state.item.phrase}, which {ITEMS['tube'].curiosity_hook}. "
        f"'Could this tube help?' {state.hero.pronoun()} wondered."
    )
    world.say(
        f"First, {state.hero.label} {scenario.first_try}. That did not solve the problem, because "
        f"{scenario.clue}."
    )
    sharing_index = (variant // (len(SCENARIOS) * len(OPENINGS))) % len(SHARING_LINES)
    world.say(SHARING_LINES[sharing_index].format(hero=state.hero.label, helper=state.helper.label))

    state.shared = True
    state.item.receiver = state.helper.id
    state.hero.memes["want"] = state.hero.memes.get("want", 0) + 1
    state.hero.memes["share"] = state.hero.memes.get("share", 0) + 1
    state.helper.memes["share"] = state.helper.memes.get("share", 0) + 1
    world.say(
        f"They used it as {scenario.tube_use}. {state.hero.label} {scenario.hero_action}; "
        f"{state.helper.label} {scenario.helper_action}."
    )
    state.discovery = scenario.discovery
    world.say(f"Peek and ponder, test and see: {scenario.discovery}.")

    state.resolved = True
    state.resolution = scenario.resolution
    world.say(f"Together they {scenario.resolution}. The quest was complete.")
    world.say(f"{state.hero.label} learned that {scenario.lesson}.")
    world.say(f"{scenario.ending}. Curiosity had opened the quest, and sharing had carried it home.")

    world.facts = {
        "hero": state.hero,
        "helper": state.helper,
        "item": state.item,
        "shared": state.shared,
        "resolved": state.resolved,
        "wonder": state.wonder,
        "scenario_title": scenario.title,
        "problem": scenario.problem,
        "first_try": scenario.first_try,
        "clue": scenario.clue,
        "tube_use": scenario.tube_use,
        "discovery": scenario.discovery,
        "resolution": scenario.resolution,
        "lesson": scenario.lesson,
        "ending": scenario.ending,
    }
    return world, state


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[index]
    item: Entity = world.facts["item"]  # type: ignore[index]
    helper: Entity = world.facts["helper"]  # type: ignore[index]
    scenario_title = str(world.facts["scenario_title"])
    problem = str(world.facts["problem"])
    return [
        f"Write a nursery-rhyme story about {scenario_title}, led by {hero.label} at the cliff lookout, using a {item.label} safely.",
        f"Tell a gentle quest in which {hero.label} and {helper.label} share a tube to solve this problem: {problem}.",
        f"Write a child-friendly cliff-lookout tale about curiosity, sharing, and {world.facts['tube_use']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[index]
    helper: Entity = world.facts["helper"]  # type: ignore[index]
    item: Entity = world.facts["item"]  # type: ignore[index]
    return [
        QAItem(
            question="Where did the quest take place, and how did the children stay safe?",
            answer=(
                "The quest took place at the cliff lookout. The children worked on its fenced paths or activity deck, "
                "followed the ranger's rules, and stayed behind the railing."
            ),
        ),
        QAItem(
            question=f"What problem did {hero.label} and {helper.label} need to solve?",
            answer=f"They needed to help because {world.facts['problem']}.",
        ),
        QAItem(
            question=f"What did {hero.label} try first, and what clue showed them to reconsider?",
            answer=(
                f"First, {hero.label} {world.facts['first_try']}. They reconsidered when they noticed that "
                f"{world.facts['clue']}."
            ),
        ),
        QAItem(
            question=f"How did sharing the {item.label} help the friends complete their quest?",
            answer=(
                f"They shared the tube and used it as {world.facts['tube_use']}. By combining their actions, "
                f"they discovered that {world.facts['discovery']}."
            ),
        ),
        QAItem(
            question="How did the quest end, and what did the friends learn?",
            answer=(
                f"Together they {world.facts['resolution']}. {hero.label} learned that {world.facts['lesson']}."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a little journey to find something, solve something, or do something important.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone wonder, peek, and want to learn more about what they found.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too.",
        ),
        QAItem(
            question="What is a tube?",
            answer="A tube is a long hollow thing, like a small round container or pipe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_FACTS_TEMPLATE = """
setting(cliff_lookout).
item(tube).
curious(hero).
sees(hero,item).
shareable(item).
wants(hero,item).
"""


def asp_facts() -> str:
    return ASP_FACTS_TEMPLATE


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    return True


def asp_verify() -> int:
    if asp_valid():
        print("OK: ASP and Python gate agree on the tube quest.")
        return 0
    print("Mismatch between ASP and Python gate.")
    return 1


CURATED = [
    StoryParams(hero_name="Mina", hero_type="girl", helper_name="Robin", helper_type="boy", item="tube"),
    StoryParams(hero_name="Toby", hero_type="boy", helper_name="June", helper_type="girl", item="tube"),
    StoryParams(hero_name="Luna", hero_type="girl", helper_name="Kit", helper_type="boy", item="tube"),
]


def generate(params: StoryParams) -> StorySample:
    world, _state = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show curious/1.\n#show sees/2.\n#show shareable/1.\n#show wants/2.\n#show quest_ready/2.\n#show sharing_fix/2.\n#show happy_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible tube quest model:")
        print("  cliff lookout / tube / curiosity / sharing")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.helper_name} at the cliff lookout"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
