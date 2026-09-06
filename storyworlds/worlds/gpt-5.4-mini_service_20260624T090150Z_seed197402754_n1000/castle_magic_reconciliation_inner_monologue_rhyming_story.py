#!/usr/bin/env python3
"""
A small storyworld about a castle, a bit of magic, a hurt feeling, and a kind
repair. The tale is written in a gentle rhyming style and driven by a simple
world model so the ending changes what the characters feel and do.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402

TITLE = "castle_magic_reconciliation_inner_monologue_rhyming_story"

CASTLE_NAMES = [
    "Moongate Castle",
    "Pebblekeep Castle",
    "Rosewind Castle",
    "Brighttower Castle",
    "Candlebrook Castle",
]

CHARACTER_NAMES = ["Milo", "Nia", "Oren", "Pia", "Lina", "Jasper", "Tessa", "Bram"]
ROLES = ["young page", "small helper", "castle child", "apprentice", "messenger"]
MAGIC_OBJECTS = ["a silver bell", "a tiny wand", "a ribbon star", "a glowing key", "a warm lantern"]
SPELLS = ["sparkle a door open", "mend a torn banner", "make a pebble sing", "light a dark stair", "turn crumbs to crumbs of gold"]
FEELINGS = ["sad", "cross", "hurt", "lonely", "worried"]
FIXES = ["say sorry", "share the spell", "listen carefully", "give back the charm", "make it right"]
SCENARIOS = [
    {
        "place": "the map room",
        "goal": "hang paper stars above the map table",
        "mistake": "sent every paper star whirling into the rafters",
        "harm": "knocked down the careful map labels {friend} had spent all morning tying",
        "evidence": "One label clung to {friend}'s sleeve while the rest sailed out of reach",
        "repair": "lower the stars one by one and retie every label beside {friend}",
        "result": "the map showed every road again",
        "image": "Two last paper stars turned slowly above the mended map",
    },
    {
        "place": "the moonlit kitchen",
        "goal": "help the cooks decorate a welcome pie",
        "mistake": "made the pie plates skate in a glittering line",
        "harm": "splashed berry filling across {friend}'s finished sugar crown",
        "evidence": "Purple drops slid from the crown as {friend} stared at the floor",
        "repair": "wipe the tables, mix fresh icing, and rebuild the crown with {friend}",
        "result": "a new sugar crown stood straight on the welcome pie",
        "image": "The friends carried the pie beneath one steady candle flame",
    },
    {
        "place": "the echoing music hall",
        "goal": "add a little magic to {friend}'s first concert",
        "mistake": "woke every brass horn before the concert began",
        "harm": "drowned out the quiet solo {friend} had practiced for weeks",
        "evidence": "The final soft note vanished beneath a hundred noisy toots",
        "repair": "hush each horn and stand beside {friend} for a second beginning",
        "result": "the quiet solo floated clearly from wall to wall",
        "image": "One silver note lingered while the candles burned low",
    },
    {
        "place": "the high tower garden",
        "goal": "make the night flowers open for the moth count",
        "mistake": "called up a gust that scattered the counting cards",
        "harm": "erased the neat tally {friend} had promised the gardener",
        "evidence": "Blank cards fluttered among the pots, and {friend}'s pencil went still",
        "repair": "search every pot, count every moth again, and let {friend} lead",
        "result": "each moth had a mark beside its flower",
        "image": "The hundredth moth folded its wings on the final checked card",
    },
    {
        "place": "the little throne-room stage",
        "goal": "brighten the scenery for a puppet play",
        "mistake": "made the painted dragon leap off its cloth",
        "harm": "tore the moon backdrop {friend} had painted for the final scene",
        "evidence": "The cloth moon lay in two pieces at {friend}'s shoes",
        "repair": "catch the paper dragon and stitch the moon while {friend} chose the thread",
        "result": "the puppet moon rose whole for the final scene",
        "image": "A patched white moon shone over the puppets' closing bow",
    },
    {
        "place": "the castle library",
        "goal": "find a missing rhyme for the librarian's new book",
        "mistake": "made all the loose words hop from page to page",
        "harm": "mixed up the poem {friend} was about to read aloud",
        "evidence": "The word 'blue' sat beside 'shoe,' but every other rhyme had fled",
        "repair": "gather the hopping words and ask {friend} where each one belonged",
        "result": "the poem returned in the order {friend} had written",
        "image": "The book closed softly with a blue ribbon marking the rescued rhyme",
    },
    {
        "place": "the rain-washed courtyard",
        "goal": "float a toy fleet across the puddles",
        "mistake": "turned one puddle into a rushing silver stream",
        "harm": "swept away the tiny boat {friend} had carved for the race",
        "evidence": "Only the boat's red flag showed beneath the drain gate",
        "repair": "stop the stream, lift the gate, and dry the little boat with {friend}",
        "result": "the red-flagged boat sailed in the race after all",
        "image": "Its red flag crossed the last puddle beside a reflection of the moon",
    },
    {
        "place": "the armor gallery",
        "goal": "polish the shields before the castle parade",
        "mistake": "set twelve empty suits of armor marching",
        "harm": "crushed the flower garland {friend} had woven for the smallest shield",
        "evidence": "Bent daisies poked from one iron boot while {friend} held the broken string",
        "repair": "halt the armor and weave a wider garland together from fresh stems",
        "result": "the smallest shield wore the brightest ring of flowers",
        "image": "A daisy nodded from the shield as the quiet parade went by",
    },
    {
        "place": "the snowy gatehouse",
        "goal": "warm the nest of a shivering castle wren",
        "mistake": "melted the snow roof faster than anyone expected",
        "harm": "soaked the wool blanket {friend} had carried up for the bird",
        "evidence": "The blanket dripped in {friend}'s hands, and the wren chirped from the sill",
        "repair": "dry the wool gently and build a wooden cover at {friend}'s side",
        "result": "the wren settled into a warm and sheltered nest",
        "image": "Three small tracks ended beneath the new roof as snow began to fall",
    },
    {
        "place": "the lantern stair",
        "goal": "guide younger children safely to the feast",
        "mistake": "filled the stair with bouncing balls of light",
        "harm": "hid the careful direction signs {friend} had placed on every turn",
        "evidence": "A lost child called from the landing while {friend} searched through the glow",
        "repair": "dim the wild lights, find the child, and follow {friend}'s signs together",
        "result": "every child reached the feast by the marked path",
        "image": "One calm lantern lit the final arrow toward the open hall",
    },
    {
        "place": "the old clock chamber",
        "goal": "help the clock strike in time for the noon picnic",
        "mistake": "sent the clock hands racing around and around",
        "harm": "spoiled the bell cue {friend} needed to open the picnic doors",
        "evidence": "The basket line waited below while {friend} counted the wrong chimes",
        "repair": "slow each gear and let {friend} call the true count",
        "result": "twelve clear chimes opened the picnic doors",
        "image": "The twelfth chime faded over twelve baskets on the grass",
    },
    {
        "place": "the glass-roofed bird room",
        "goal": "teach the castle ravens a birthday tune",
        "mistake": "made the ravens repeat every sound at once",
        "harm": "buried {friend}'s gentle flute tune beneath a storm of echoes",
        "evidence": "The flute lowered, but one raven kept copying {friend}'s unhappy sigh",
        "repair": "quiet the echoes and teach the tune one note at a time with {friend}",
        "result": "the ravens sang the birthday tune in a bright little chorus",
        "image": "A black feather drifted onto the final note of {friend}'s music sheet",
    },
]

OPENINGS = [
    "In {castle}, morning windows caught the light;\n{hero}, the {role}, planned a magical delight.",
    "Rain tapped the roof of {castle} that day;\n{hero}, the {role}, had a spell to play.",
    "A bell welcomed dawn at {castle}'s wall;\n{hero}, the {role}, hurried down the hall.",
    "At {castle}, flags danced high in the air;\n{hero}, the {role}, had magic to share.",
    "Soft moonbeams silvered {castle}'s old stone;\n{hero}, the {role}, practiced a spell alone.",
    "{castle} woke to a skylark's song;\n{hero}, the {role}, hoped magic would help things along.",
    "Warm kitchen bells rang through {castle} bright;\n{hero}, the {role}, held a charm very tight.",
    "Beyond {castle}'s windows, clouds sailed blue;\n{hero}, the {role}, had magical work to do.",
]

THOUGHTS = [
    "Inside, {hero} thought, 'I wanted cheers, not tears.\nI rushed past my friend and ignored all their fears.'",
    "{hero}'s inner monologue whispered, 'That look tells me why: freed magic is easy, but trust can run dry.'",
    "'My spell caused this trouble; I see it at last,' {hero} thought. 'Being clever means learning, not hiding the past.'",
    "A thought tapped inside {hero}'s mind like a bell: 'Ask what was hurt, then listen well.'",
    "'I meant to bring wonder, yet caused this sad sight. I must face what I changed and help set it right,' {hero} thought.",
    "Deep in {hero}'s thoughts came a brave little start: 'A true magic mend must begin with the heart.'",
    "{hero} thought, 'If I make an excuse and race on, the spell may be fixed but our friendship is gone.'",
    "'I chose on my own, so the trouble is mine. I'll listen to {friend}'s plan and follow their sign,' {hero} thought.",
]

ENDINGS = [
    "That was reconciliation, patient and true: not hiding a mistake, but repairing it through.\n{image}.",
    "The castle grew peaceful as evening drew near; trust had returned because both friends could hear.\n{image}.",
    "No grander enchantment lit tower or hall than making things right after causing a fall.\n{image}.",
    "Their quarrel was over, their friendship made bright; reconciliation had changed wrong into right.\n{image}.",
    "The best castle magic was plain to behold: a truth bravely spoken and kindness retold.\n{image}.",
    "Together they learned what a good repair brings: room for two voices and care for small things.\n{image}.",
    "Forgiveness came softly, not quick as a spell; it grew from kind actions done carefully well.\n{image}.",
    "So magic brought wonder, but friendship brought more: two helpers stood smiling where hurt stood before.\n{image}.",
]
RHYMES = {
    "castle": "brassel",
    "magic": "tragic",
    "reconciliation": "restoration",
    "monologue": "dialogue",
    "spark": "lark",
    "glow": "flow",
    "stone": "tone",
    "light": "bright",
    "heart": "start",
    "kind": "mind",
}

ASP_RULES = r"""
castle(castle_one).
room(courtyard).
room(hall).
room(tower).
character(hero).
character(friend).
magic_item(charm).
feeling(sad).
feeling(hurt).

can_use_magic(hero,charm).
can_break_trust(hero,friend) :- can_use_magic(hero,charm).
needs_reconciliation(hero,friend) :- can_break_trust(hero,friend), feeling(hurt).
can_reconcile(hero,friend) :- needs_reconciliation(hero,friend).
resolved(hero,friend) :- can_reconcile(hero,friend).
#show needs_reconciliation/2.
#show resolved/2.
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    castle: str
    hero: str
    friend: str
    role: str
    magic_object: str
    spell: str
    feeling: str
    fix: str
    seed: Optional[int] = None


@dataclass
class World:
    castle: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Castle magic reconciliation rhyming storyworld.")
    ap.add_argument("--castle", choices=["castle"])
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
    castle = args.castle or "castle"
    hero = rng.choice(CHARACTER_NAMES)
    friend = rng.choice([n for n in CHARACTER_NAMES if n != hero])
    role = rng.choice(ROLES)
    magic_object = rng.choice(MAGIC_OBJECTS)
    spell = rng.choice(SPELLS)
    feeling = rng.choice(FEELINGS)
    fix = rng.choice(FIXES)
    return StoryParams(
        castle=castle,
        hero=hero,
        friend=friend,
        role=role,
        magic_object=magic_object,
        spell=spell,
        feeling=feeling,
        fix=fix,
    )


def _build_world(params: StoryParams) -> World:
    castle_index = (params.seed or 0) % len(CASTLE_NAMES)
    world = World(castle=CASTLE_NAMES[castle_index])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.role, label=params.hero))
    friend = world.add(Entity(id=params.friend, kind="character", type="friend", label=params.friend))
    charm = world.add(Entity(id="charm", type="magic_object", label=params.magic_object, phrase=params.magic_object, owner=hero.id))
    hero.memes["joy"] = 1
    friend.memes["trust"] = 1
    world.facts.update(hero=hero, friend=friend, charm=charm, params=params)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    charm: Entity = world.facts["charm"]
    rng = random.Random((params.seed or 0) ^ 0xCA571E)
    scenario = dict(rng.choice(SCENARIOS))
    details = {
        "castle": world.castle,
        "hero": hero.id,
        "friend": friend.id,
        "role": params.role,
        "object": charm.label,
        "spell": params.spell,
        **scenario,
    }
    scenario = {key: value.format(**details) for key, value in scenario.items()}
    details.update(scenario)

    world.say(rng.choice(OPENINGS).format(**details))
    world.say(
        rng.choice(
            [
                "In {place}, {friend} was ready to {goal}.\n'{hero}, will you help?' came the hopeful reply.",
                "The two friends met in {place} with work to begin: they hoped to {goal}, and both longed to win.",
                "A castle job waited in {place} that noon: {friend} hoped to {goal}, and {hero} came soon.",
                "'{goal_cap},' said {friend} with care.\n{hero} raised {object}. 'My magic can help us there!'",
                "Down in {place}, a promise was due: {friend} would {goal}, with help from {hero} too.",
                "The plan in {place} was modest and clear: {goal}, with one helpful friend standing near.",
            ]
        ).format(goal_cap=scenario["goal"].capitalize(), **details)
    )

    world.para()
    world.say(
        rng.choice(
            [
                "But {hero} hurried ahead before asking what to do. To {spell}, they waved {object}; a fizzing wind blew.",
                "'Please wait for my signal,' {friend} started to say. But {hero} tried to {spell}, and magic leaped away.",
                "Wanting the glory, {hero} stepped out alone and used {object} with a bright ringing tone.",
                "The careful plan needed two voices in time, yet {hero} began with a solo spell-rhyme.",
                "{friend} reached for the plan, but {hero} reached first: {object} flashed once, and the loose magic burst.",
                "'I know how to {spell}!' {hero} cried with delight, and cast before checking if all was just right.",
            ]
        ).format(**details)
    )
    world.say(f"The spell {scenario['mistake']}; it {scenario['harm']}.")
    world.say(f"{scenario['evidence']}.")
    friend.memes[params.feeling] = 1
    hero.memes["pride"] = 1

    world.para()
    world.say(
        rng.choice(
            [
                "'{hero}, I feel {feeling},' said {friend}. 'You rushed on alone.' The words felt much heavier than turret stone.",
                "{friend} said, 'I feel {feeling}. My work mattered too.' {hero}'s proud little answer shrank before it was through.",
                "'I am {feeling},' whispered {friend}. 'You did not wait.' The castle clock ticked while {hero} looked at the state.",
                "{friend} did not shout, but their voice sounded small: 'I feel {feeling}; you did not hear me at all.'",
                "'The magic was dazzling, but I feel {feeling},' said {friend}. 'A helper should listen before they begin.'",
            ]
        ).format(feeling=params.feeling, **details)
    )
    world.say(rng.choice(THOUGHTS).format(**details))
    hero.memes["remorse"] = 1
    friend.memes["hurt"] = 1

    world.para()
    world.say(
        rng.choice(
            [
                "'I am sorry I rushed and ignored what you said,' {hero} replied. 'I will {fix}, then follow your lead.'",
                "{hero} lowered {object}. 'I caused this,' they said. 'May I {fix} and help with your plan instead?'",
                "'No spell can excuse me,' said {hero}. 'That is true. I will {fix}, and the next choice belongs to you.'",
                "{hero} faced {friend}. 'I see why you hurt. I will {fix}, then stay for the patient work.'",
                "'I cared more for showing my magic than you,' {hero} said. 'I will {fix}, and repair what I threw askew.'",
                "{hero} put the charm down where both friends could see. 'I'll {fix}. Will you mend this with me?'",
            ]
        ).format(fix=params.fix, **details)
    )
    world.say(
        rng.choice(
            [
                "Not with a shortcut or one flashy spell, they worked to {repair}, and worked at it well.",
                "Then shoulder to shoulder, with no boastful sound, they began to {repair} on the ground.",
                "{friend} named the first step; {hero} answered, 'All right.' Together they started to {repair} before night.",
                "The apology opened a door, but their actions went through: they stayed to {repair}, both seeing it through.",
                "A promise needs footsteps, not only a rhyme, so they chose to {repair}, taking their time.",
                "Magic rested quietly while patient hands learned to {repair}, following careful commands.",
            ]
        ).format(**details)
    )

    friend.memes["forgive"] = 1
    friend.memes["hurt"] = 0
    friend.memes[params.feeling] = 0
    friend.memes["trust"] = 2
    hero.memes["peace"] = 1
    hero.memes["remorse"] = 0
    world.say(
        rng.choice(
            [
                "At last, {result}. '{hero}, I forgive you,' said {friend}. 'We repaired it together.'",
                "Soon {result}. {friend}'s smile returned: 'Next time, let us plan the magic together.'",
                "When {result}, {friend} nodded. 'Your listening helped more than a spell.'",
                "By supper, {result}. 'We are friends again,' said {friend}, and this time {hero} listened well.",
                "Before the last bell, {result}. {friend} offered {object} back: 'We can share its magic now.'",
            ]
        ).format(**details)
    )
    world.para()
    world.say(rng.choice(ENDINGS).format(**details))

    world.facts.update(
        resolved=True,
        scenario=scenario,
        mistake=scenario["mistake"],
        harm=scenario["harm"],
        repair=scenario["repair"],
        result=scenario["result"],
        ending_image=scenario["image"],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f'Write a short rhyming story set in a castle where {p.hero} uses magic in {scenario["place"]} and then makes things right.',
        f"Tell a gentle castle tale about {p.hero} and {p.friend}, using an inner monologue to turn a mistake into reconciliation.",
        f'Write a child-friendly rhyme using the word "castle," a sincere apology, and a concrete ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    scenario = world.facts["scenario"]
    qa = [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in {world.castle}, especially in {scenario['place']}, where {p.hero} and {p.friend} try to complete a castle job.",
        ),
        QAItem(
            question=f"What went wrong when {p.hero} used the magic?",
            answer=f"The spell {scenario['mistake']}. As a result, it {scenario['harm']}.",
        ),
        QAItem(
            question=f"What did {p.hero} realize during the inner monologue?",
            answer=f"{p.hero} realized that rushing ahead had hurt {p.friend}. A real repair required listening and responsible action, not another quick spell.",
        ),
        QAItem(
            question=f"How did {p.hero} and {p.friend} reconcile?",
            answer=f"{p.hero} promised to {p.fix}, and together they worked to {scenario['repair']}. By the end, {scenario['result']}, and the friends trusted each other again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a castle?",
            answer="A castle is a large strong building with walls and rooms where people can live or gather in a story.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset, make peace, and feel close again after a hurt feeling.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking someone does in their own mind when they think about what to do.",
        ),
        QAItem(
            question="Why can magic be tricky in a story?",
            answer="Magic can be tricky because it can change things very fast, so someone may need to think carefully before using it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(castle="castle", hero="Milo", friend="Nia", role="young page", magic_object="a silver bell", spell="sparkle a door open", feeling="sad", fix="say sorry"),
    StoryParams(castle="castle", hero="Lina", friend="Oren", role="apprentice", magic_object="a glowing key", spell="light a dark stair", feeling="hurt", fix="listen carefully"),
]


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("castle", "castle_one"),
        asp.fact("character", "hero"),
        asp.fact("character", "friend"),
        asp.fact("magic_item", "charm"),
        asp.fact("feeling", "sad"),
        asp.fact("feeling", "hurt"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/2."))
    atoms = set(asp.atoms(model, "resolved"))
    expected = {("hero", "friend")}
    if atoms == expected:
        print("OK: ASP twin matches the reasonableness gate.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(expected))
    return 1


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
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/2."))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
