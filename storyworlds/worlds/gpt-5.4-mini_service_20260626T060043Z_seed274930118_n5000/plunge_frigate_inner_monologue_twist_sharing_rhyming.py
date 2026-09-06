#!/usr/bin/env python3
"""
A tiny storyworld for a rhyming tale about a frigate, a plunge, a twist, and sharing.

Premise:
- A small crew sails a bright frigate.
- The hero wants to make a daring plunge into the sparkling harbor.
- A twist reveals the best prize is something to share, not keep.
- Inner monologue is used to show the hero thinking.
- The ending proves the change through a shared action.
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
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    hero: str = "Milo"
    companion: str = "Nia"
    vessel: str = "the frigate"
    place: str = "the harbor"
    prize: str = "a silver shell"
    arc: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    hero: Entity
    companion: Entity
    vessel: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HERO_NAMES = ["Milo", "Tia", "Pip", "Rory", "Lina", "Jude"]
COMPANION_NAMES = ["Nia", "Pax", "June", "Sora", "Bea", "Kai"]
PRIZES = [
    "a silver shell",
    "a shiny star map",
    "a pearl ribbon",
    "a small gold bell",
]
PLACES = ["the harbor", "the quiet bay", "the moonlit dock"]


ARCS = [
    {
        "premise": "The crew was charting singing buoys before the morning fog arrived",
        "problem": "the last buoy had drifted beyond a curtain of mist",
        "stake": "Without it, the fishing boats could miss the safe channel home",
        "temptation": "dive alone, grab its chain, and claim the captain's ribbon",
        "clue": "a bell answered from much nearer than the chart suggested",
        "action": "They tied a bright guide rope, rang the deck bell, and followed its echo together",
        "twist": "the missing buoy was not lost at all; a young seal had tangled its chain around a piling",
        "sharing": "They freed the seal and shared the ribbon among every lookout who had listened",
        "lesson": "a careful crew can find what a hurried hero overlooks",
        "ending": "the rescued buoy blinked beside the frigate while the seal drew silver circles in the wake",
        "question": "Why did the crew need to find the final buoy?",
        "answer": "They needed it to mark the safe channel so the fishing boats could come home through the fog.",
    },
    {
        "premise": "A school of lantern fish gathered below the frigate for the Moonwake Parade",
        "problem": "their leader's little lamp had gone dark",
        "stake": "The underwater parade would lose its path beneath the ship",
        "temptation": "plunge after the brightest fish and keep its glow in a jar",
        "clue": "each fish shone more strongly whenever another fish swam close",
        "action": "They lowered mirrored spoons and turned the deck lanterns toward the waves",
        "twist": "the leader did not need a new lamp; the whole school could lend one another light",
        "sharing": "They shared the frigate's lantern glow until every small fin carried a gleam",
        "lesson": "light grows useful when nobody tries to own it",
        "ending": "green and gold fish stitched a shining ribbon around the frigate's dark hull",
        "question": "What made the lantern fish shine more strongly?",
        "answer": "The lantern fish shone more strongly when they gathered close and shared light.",
    },
    {
        "premise": "The frigate carried seed cakes to an island garden after a long dry week",
        "problem": "a sudden plunge in temperature froze the fresh-water barrel's tap",
        "stake": "The seedlings would wilt if the delivery arrived without water",
        "temptation": "hide the last warm cup and save it for the fastest sailor",
        "clue": "steam curled from every crew member's breakfast mug",
        "action": "They poured one sip from each mug around the tap and wrapped it in a shared scarf",
        "twist": "no single cup was enough, but all the tiny gifts together thawed the barrel",
        "sharing": "They divided both the water and the seed cakes fairly at the island garden",
        "lesson": "small offerings can solve a large problem when they meet",
        "ending": "newly watered leaves tapped the empty mugs like quiet green drums",
        "question": "How did the crew thaw the frozen tap?",
        "answer": "Everyone shared a little warm drink and wrapped the tap until their combined warmth thawed it.",
    },
    {
        "premise": "Young mapmakers came aboard the frigate to sketch the cliffs",
        "problem": "a gust snatched their only finished map toward the water",
        "stake": "The class would have no chart for its journey back",
        "temptation": "make a showy plunge and rescue the map without asking for help",
        "clue": "the paper kept circling beside a loose square of sailcloth",
        "action": "They stretched the sailcloth between two oars and scooped from opposite rails",
        "twist": "the wet map's ink printed a perfect reverse copy onto the cloth",
        "sharing": "They cut the cloth into guide patches so every mapmaker carried the route",
        "lesson": "a mistake can become a gift when people solve it together",
        "ending": "twelve little map patches fluttered from twelve packs as the frigate turned for home",
        "question": "What surprising copy appeared after the map got wet?",
        "answer": "The wet map printed a reversed copy of the route onto the loose sailcloth.",
    },
    {
        "premise": "The frigate's cook prepared berry buns for boats sheltering from a storm",
        "problem": "the mixing bowl slid across the deck toward an open hatch",
        "stake": "The waiting crews would have no warm supper",
        "temptation": "plunge across the slick boards and catch the bowl single-handed",
        "clue": "the rolling bowl slowed whenever it crossed a coil of rope",
        "action": "They made a zigzag of spare ropes while the cook guided the bowl with a wooden spoon",
        "twist": "the bowl stopped safely, but the tumble had braided the berries into a star",
        "sharing": "They baked the starry batter into small buns and passed a basket to every boat",
        "lesson": "helping hands make a safer rescue and a wider feast",
        "ending": "warm berry stars glowed in cabin windows all around the anchored frigate",
        "question": "Why did the crew place ropes across the deck?",
        "answer": "They used the ropes to slow and safely stop the mixing bowl before it reached the hatch.",
    },
    {
        "premise": "A timid whale calf followed the frigate into a shallow cove",
        "problem": "the falling tide left the calf unsure which channel led back to sea",
        "stake": "It could be stranded when the water made its next plunge",
        "temptation": "race ahead alone and be praised as the whale's rescuer",
        "clue": "the calf copied two soft taps made against the hull",
        "action": "They shared the work: one watched the depth, one tapped, and the crew eased the frigate seaward",
        "twist": "a second set of taps came from the calf's mother beyond the rocks",
        "sharing": "They passed the tapping rhythm from ship to calf until mother and calf found each other",
        "lesson": "guidance works best when everyone listens as well as leads",
        "ending": "two whale tails rose together and sprinkled the frigate with a bright farewell",
        "question": "How did the crew guide the whale calf?",
        "answer": "They tapped a gentle rhythm on the hull and steered through the deep channel while watching the depth.",
    },
    {
        "premise": "The frigate hosted a floating library for children along the coast",
        "problem": "a crate of picture books tipped open during a sharp turn",
        "stake": "several books skated toward the foaming edge of the deck",
        "temptation": "plunge after the rarest book and leave the ordinary ones behind",
        "clue": "the children's long reading blankets were still folded beside the mast",
        "action": "They linked the blankets into a soft net while the children called which corner to lift",
        "twist": "the plainest-looking book contained blank pages for the whole town's stories",
        "sharing": "They dried every book and invited each child to add one page to the blank volume",
        "lesson": "the best story can be the one with room for every voice",
        "ending": "the new book rested open under the mast, crowded with fresh ink and careful fingerprints",
        "question": "What was special about the plain-looking book?",
        "answer": "Its pages were blank, so every child could contribute a story to it.",
    },
    {
        "premise": "The frigate entered a friendly race around three rocky islands",
        "problem": "a rival skiff snapped its little mast in the first hard wind",
        "stake": "Its crew was drifting toward choppy water",
        "temptation": "plunge onward to win while nobody could catch them",
        "clue": "the prize pennant was exactly as long as the skiff's broken brace",
        "action": "They turned back, lowered a rope ladder, and lashed the pennant beside the cracked mast",
        "twist": "the race judge counted the rescue as the finest finish of all",
        "sharing": "Both crews crossed the line together and shared the picnic meant for the winners",
        "lesson": "winning matters less than refusing to leave a neighbor behind",
        "ending": "two boats reached the bell side by side, with one patched pennant snapping above them",
        "question": "Why did the frigate turn back during the race?",
        "answer": "The frigate turned back because the rival skiff had broken its mast and was drifting toward rough water.",
    },
    {
        "premise": "A rain cloud followed the frigate while every other patch of sky stayed blue",
        "problem": "the deck instruments were getting soaked before the evening concert",
        "stake": "The island audience might hear no music at all",
        "temptation": "plunge below deck with the driest drum and protect only one part",
        "clue": "the cloud paused whenever the crew played a low, gentle note",
        "action": "They passed out cups and spoons so every sailor could join a quiet rhythm",
        "twist": "the lonely cloud had followed because it wanted to be part of the band",
        "sharing": "They gave the cloud the rain-beat and shared the covered instruments with the whole crew",
        "lesson": "an interruption may be an invitation we have not understood",
        "ending": "the cloud drummed one last drop into each cup, then opened a rainbow over the frigate",
        "question": "Why had the rain cloud followed the frigate?",
        "answer": "The cloud was lonely and wanted to join the crew's music.",
    },
    {
        "premise": "The frigate searched for a bell said to ring beneath the reef",
        "problem": "every sailor heard the sound from a different direction",
        "stake": "Following the wrong echo could scrape the ship against coral",
        "temptation": "take a reckless plunge overboard and hunt for the bell alone",
        "clue": "the echoes matched the clink of breakfast spoons inside the cabin",
        "action": "They stopped the engines, shared listening posts, and compared the timing of each ring",
        "twist": "there was no sunken bell; a spoon had slipped into a swinging lantern",
        "sharing": "They used the funny rhythm to compose a reef song and taught every sailor a verse",
        "lesson": "wonder grows stronger, not weaker, when evidence changes the answer",
        "ending": "the harmless spoon chimed above a reef left clear and unbroken",
        "question": "What was really making the mysterious bell sound?",
        "answer": "A breakfast spoon inside a swinging lantern was making the sound.",
    },
    {
        "premise": "The frigate delivered painted kites for the cliff-top wind festival",
        "problem": "one enormous kite pulled free and wrapped its tail around the anchor winch",
        "stake": "The tangled winch could not lift the anchor before the tide turned",
        "temptation": "plunge at the knot with a knife and cut away everyone else's kite tails",
        "clue": "each colored tail loosened when its owner held the matching ribbon steady",
        "action": "They called the kite makers aboard and passed each ribbon back to the hands that knew it",
        "twist": "the untangled tails formed a map of the safest wind path up the cliff",
        "sharing": "They tied the ribbons into one long festival streamer after freeing the winch",
        "lesson": "asking owners to share their knowledge can untie more than force",
        "ending": "the long streamer climbed from frigate to cliff, bright against the turning tide",
        "question": "How did the crew untangle the kite tails?",
        "answer": "Each kite maker steadied a matching ribbon while the crew loosened the tails in order.",
    },
    {
        "premise": "The frigate carried a tiny orchard in pots to a bare lighthouse island",
        "problem": "one wave made the pots plunge and slide toward the lower rail",
        "stake": "The young trees could tumble into the salty sea",
        "temptation": "save the tallest tree first because it would earn the biggest prize",
        "clue": "the smallest pots fit snugly between the larger ones",
        "action": "They formed a passing line and nested every little pot between two sturdy neighbors",
        "twist": "the smallest tree was the only one already carrying a ripe pear",
        "sharing": "They sliced the pear into tasting pieces and planted every tree around the lighthouse",
        "lesson": "size does not decide worth, and safety can come from standing together",
        "ending": "at sunset, one pear seed lay tucked in new soil while the frigate's sail waved offshore",
        "question": "Why were the small pots useful during the rescue?",
        "answer": "The small pots fit between the large ones and helped brace the whole group of trees.",
    },
]

OPENINGS = [
    "Morning made the brass rails gleam and the gulls wheel high",
    "Under a peach-colored sky, the wake unrolled white",
    "With canvas humming overhead, the bright deck came alive",
    "A salty breeze skipped over the bow and tugged every cap",
    "Sunlight hopped from wave to window as the ship left the quay",
    "The tide tapped time on the hull while the rigging sang",
    "Beyond the breakwater, blue water opened wide",
    "At first bell, the sea lay smooth as a sheet of glass",
]

THOUGHT_LEADS = [
    "Inside, one thought knocked louder than the waves",
    "A private rhyme began to pace through {hero}'s mind",
    "Before moving, {hero} listened to the small voice within",
    "Two choices seesawed in {hero}'s thoughts",
    "For one quiet breath, {hero} argued with a hasty wish",
    "The deck was noisy, but {hero}'s inner monologue was clearer",
    "A brave-looking shortcut sparkled in {hero}'s imagination",
    "{hero} gripped the rail and let the next thought finish",
]

DECISIONS = [
    "'A splash made for praise may be foolish and rash; I'll ask for a plan before making a splash.'",
    "'If I hurry for glory, our trouble may grow; if we pool what we notice, the right way may show.'",
    "'I could leap for the prize and pretend I am bold, or listen and help so no friend is left cold.'",
    "'One daring dive might make everyone cheer, but sharing the thinking may make the way clear.'",
    "'Should I chase after credit and plunge on my own? No, a safer solution is rarely lone.'",
    "'The quickest bright answer may not be the best; I'll hear every helper, then put it to test.'",
    "'I want to be first, yet I know what is true: a crew solves a puzzle by thinking it through.'",
    "'My heart says go racing; my good sense says wait. A plan shared with friends need not arrive late.'",
]

TWIST_REACTIONS = [
    "{companion} blinked, then laughed with relief",
    "{companion} pointed, and the whole crew leaned near",
    "For a beat, even the gulls seemed to hush",
    "{companion} clapped both hands as the truth came clear",
    "The crew traded surprised looks across the deck",
    "{companion} gave a delighted whistle",
]

CODAS = [
    "{hero} kept no prize apart; the fairest reward was the work in each heart.",
    "{hero} smiled at the crew: 'What we share can repair, and the joy that comes back is enough for us all.'",
    "No one called it one sailor's success; they named every helper and shared the happiness.",
    "The lesson felt steady beneath {hero}'s feet: shared courage and kindness had made the day complete.",
    "{hero} saw that a treasure can multiply there, whenever its purpose and pleasure are shared.",
    "From that day, the crew used a saying at sea: 'A triumph for you can be welcome for me.'",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming storyworld with a frigate, a plunge, a twist, and sharing."
    )
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--companion", choices=COMPANION_NAMES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(HERO_NAMES)
    companion = args.companion or rng.choice([n for n in COMPANION_NAMES if n != hero])
    place = args.place or rng.choice(PLACES)
    prize = args.prize or rng.choice(PRIZES)
    if hero == companion:
        raise StoryError("The hero and companion must be different characters.")
    return StoryParams(
        hero=hero,
        companion=companion,
        vessel="the frigate",
        place=place,
        prize=prize,
        arc=rng.randrange(len(ARCS)),
    )


def choose(rng: random.Random, options: list[str], **values: str) -> str:
    return rng.choice(options).format(**values)


def lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def build_world(params: StoryParams) -> World:
    hero = Entity(name=params.hero, kind="hero")
    companion = Entity(name=params.companion, kind="companion")
    vessel = Entity(name=params.vessel, kind="vessel")
    return World(params=params, hero=hero, companion=companion, vessel=vessel)


def simulate(world: World) -> None:
    p = world.params
    h = world.hero
    c = world.companion
    arc = ARCS[p.arc]
    rng = random.Random(p.seed)

    h.memes["curiosity"] = 1.0
    h.memes["want_plunge"] = 1.0
    world.facts["prize"] = p.prize
    world.facts["place"] = p.place
    world.facts["vessel"] = p.vessel
    world.facts["problem"] = arc["problem"]
    world.facts["clue"] = arc["clue"]
    world.facts["lesson"] = arc["lesson"]

    opening = choose(rng, OPENINGS, hero=h.name, companion=c.name)
    world.say(
        f"{opening}. At {p.place}, {h.name} and {c.name} served aboard {p.vessel}, "
        f"where ropes went creak and clean waves streaked."
    )
    world.say(f"{arc['premise']}. Their promised prize was {p.prize}, tucked safely by the wheel.")
    world.para()

    world.say(f"Then {arc['problem']}. {arc['stake']}.")
    world.say(f"For one glittering moment, {h.name} wanted to {arc['temptation']}.")
    world.say("The choice felt like a plunge: rush for praise, or pause and share the load.")
    thought_lead = choose(rng, THOUGHT_LEADS, hero=h.name, companion=c.name)
    decision = choose(rng, DECISIONS, hero=h.name, companion=c.name)
    world.say(f"{thought_lead}. {h.name} thought, {decision}")
    h.memes["hesitation"] = 1.0
    world.facts["temptation"] = arc["temptation"]

    world.para()
    clue_starts = [
        f"{c.name} asked everyone to pause and look again",
        f"Instead of leaping, {h.name} invited {c.name} to compare clues",
        f"The two friends crouched by the rail and listened before acting",
        f"{c.name} gathered the crew, because four sharp eyes could notice more than two",
        f"They checked the deck, the water, and one another's ideas",
        f"{h.name} repeated the problem aloud, and {c.name} noticed what haste had hidden",
    ]
    world.say(f"{choose(rng, clue_starts, hero=h.name, companion=c.name)}: {arc['clue']}.")
    world.say(f"{arc['action']}.")
    reaction = choose(rng, TWIST_REACTIONS, hero=h.name, companion=c.name)
    world.say(f"Here came the twist: {arc['twist']}. {reaction}.")
    c.memes["sharing"] = 1.0
    h.memes["surprise"] = 1.0
    h.memes["sharing"] = 1.0
    world.facts["twist"] = True
    world.facts["twist_reveal"] = arc["twist"]
    world.facts["solution"] = arc["action"]

    world.para()
    world.say(f"With danger past, sharing became the finest part. {arc['sharing']}.")
    coda = choose(rng, CODAS, hero=h.name, companion=c.name)
    world.say(f"{coda} {h.name} understood that {arc['lesson']}.")
    world.say(f"As evening settled, {arc['ending']}.")
    world.facts["resolved"] = True
    world.facts["shared"] = True
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a short rhyming story about {params.hero} aboard a frigate who considers a plunge and chooses teamwork.",
        f"Tell a gentle tale in {params.place} where a surprising twist teaches {params.hero} and {params.companion} about sharing.",
        f"Make a child-friendly frigate adventure about this problem: {arc['problem']}.",
    ]
    story_qa = [
        QAItem(
            question=f"What risky shortcut did {params.hero} first consider?",
            answer=f"{params.hero} first considered trying to {arc['temptation']}.",
        ),
        QAItem(
            question=f"On {params.hero} and {params.companion}'s voyage, {lower_first(arc['question'])}",
            answer=f"During their voyage, {lower_first(arc['answer'])}",
        ),
        QAItem(
            question=f"What clue helped {params.hero} and {params.companion} choose a better plan?",
            answer=f"The useful clue {params.hero} and {params.companion} shared was that {arc['clue']}.",
        ),
        QAItem(
            question=f"What twist surprised {params.hero} and {params.companion}?",
            answer=f"{params.hero} and {params.companion} discovered that {arc['twist']}, so they could solve the real problem instead of following the first plan.",
        ),
        QAItem(
            question=f"What lesson did {params.hero} learn about sharing?",
            answer=f"{params.hero} learned that {arc['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a frigate?",
            answer="A frigate is a sailing ship that can carry a crew across the water.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else enjoy something with you instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what the characters thought would happen.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.companion, world.vessel]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.name:10} ({ent.kind:9}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
valid(story).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([asp.fact("domain", "frigate"), asp.fact("feature", "inner_monologue"), asp.fact("feature", "twist"), asp.fact("feature", "sharing")])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    if asp.atoms(model, "valid") == [("story",)]:
        print("OK: ASP twin is consistent.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


CURATED = [
    StoryParams(hero="Milo", companion="Nia", place="the harbor", prize="a silver shell", arc=0, seed=101),
    StoryParams(hero="Tia", companion="Pax", place="the quiet bay", prize="a shiny star map", arc=5, seed=202),
    StoryParams(hero="Rory", companion="June", place="the moonlit dock", prize="a pearl ribbon", arc=10, seed=303),
]


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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
