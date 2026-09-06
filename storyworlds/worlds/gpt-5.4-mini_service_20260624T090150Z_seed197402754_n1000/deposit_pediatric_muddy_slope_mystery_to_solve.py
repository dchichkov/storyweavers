#!/usr/bin/env python3
"""
A standalone storyworld: a pirate tale on a muddy slope, with a mystery to
solve, a bit of sharing, and a touch of magic.

The seed tale behind this world:
---
A small pirate crew found a muddy slope beside the harbor. Their little chest
held a strange deposit stamped with a blue star. No one knew where it came
from. A pediatric healer nearby said the chest should be opened carefully, but
the crew first had to solve the mystery of the glowing deposit, share the tools
fairly, and trust a little magic to guide them uphill.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "girl-pirate"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "boy-pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the muddy slope"


@dataclass
class StoryParams:
    name: str
    crew_name: str
    helper_name: str
    incident_id: int = 0
    telling_mode: int = 0
    clue_mode: int = 0
    response_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTING = Setting(place="the muddy slope")

NAMES = ["Finn", "Mira", "Pip", "Nell", "Ari", "Cora", "Bo", "Tess"]
CREW = ["the little crew", "the salty crew", "the bright crew"]
HELPERS = ["Dr. Marina", "Dr. Imani", "Nurse Nell", "Dr. Sol"]

HELPER_ROLES = {
    "Dr. Marina": "a pediatrician from the harbor clinic",
    "Dr. Imani": "a pediatrician making a harbor visit",
    "Nurse Nell": "a pediatric nurse from the harbor clinic",
    "Dr. Sol": "a pediatrician who cared for the island's children",
}

INCIDENTS = [
    {
        "find": "a fan-shaped deposit of blue clay blocking the clinic's rain channel",
        "mystery": "why clean water was spilling across the path instead of reaching the garden barrel",
        "risk": "The wet clay had made the muddy slope slick, so everyone stopped behind a rope on level ground.",
        "false": "At first the crew blamed a burrowing crab and nearly searched the bank for its tunnel.",
        "clue": "three tiny leaf prints pressed into the clay and a twig wedged beneath the gutter",
        "cause": "A storm had washed leaves into the gutter; the backed-up water laid down the clay deposit.",
        "action": "From the dry path, the crew passed a long hook to the adult harbor keeper, who cleared the gutter while the children held the warning rope.",
        "result": "Water burbled into the barrel again, and the clinic path began to drain.",
        "lesson": "A careful clue can correct a quick guess.",
        "image": "At dusk, one last drop rang in the barrel while their blue handprint flag dried beside the clear path.",
    },
    {
        "find": "a paper deposit slip sealed inside a bottle beside a wheel rut",
        "mystery": "who had left it there and whether it belonged to the pediatric clinic's medicine fund",
        "risk": "The bottle lay below a crumbly edge, so the crew viewed it through a spyglass instead of scrambling down.",
        "false": "A faded anchor mark made them suspect a boastful treasure hunter.",
        "clue": "a clinic stamp, yesterday's date, and a trail of cart-wheel marks leading from the dock office",
        "cause": "A gust had lifted the clinic courier's empty deposit slip from a cart before the money was taken to the bank.",
        "action": "The crew fetched the harbor keeper, who used a litter grabber from the firm path; then they compared the slip with the clinic ledger.",
        "result": "The harmless paper was returned, and the clinic confirmed that no money had been lost.",
        "lesson": "Checking records is wiser than inventing a culprit.",
        "image": "The bottle became a tiny vase on the clerk's sill, holding one white harbor daisy above the balanced ledger.",
    },
    {
        "find": "a glittering salt deposit around the mouth of an old copper pipe",
        "mystery": "why the slope sparkled even though nobody had scattered treasure",
        "risk": "Nobody tasted or touched the unknown crystals, and the crew kept younger children on the boardwalk.",
        "false": "Pip wondered whether a sea fairy had spilled a pouch of sugar.",
        "clue": "a slow drip, a green stain on the pipe, and crystals only where the morning sun dried the water",
        "cause": "Mineral-rich spring water leaked from the pipe and left a salt deposit as it evaporated.",
        "action": "The crew marked the leak with a bright pennant and guided the island plumber to it along the safe path.",
        "result": "The plumber closed the valve and repaired the joint before the trickle could deepen the mud.",
        "lesson": "Unknown substances should be observed, not sampled.",
        "image": "By moonrise, the repaired pipe was quiet and a single harmless crystal gleamed inside a labeled display jar.",
    },
    {
        "find": "a round deposit of yellow pollen on the clinic's blue supply crate",
        "mystery": "how the powder appeared while the crate was covered",
        "risk": "Because pollen can bother some people's breathing, the crew did not blow it into the air.",
        "false": "The neat circle looked so exact that they first suspected a stamped secret message.",
        "clue": "bee tracks, a loose corner of canvas, and yellow dust on the nearby sunflowers",
        "cause": "A bee had crawled beneath the canvas during the rain and shaken pollen onto the crate.",
        "action": "Following the clinician's guidance, the crew gave the bee space while an adult wiped the sealed crate with a damp cloth.",
        "result": "The bee flew back to the flowers, and the clean supplies remained safely closed.",
        "lesson": "Kind observation can solve a mystery without disturbing a small visitor.",
        "image": "Sunset warmed the dry crate while the bee vanished into a sunflower as golden as a captain's button.",
    },
    {
        "find": "a pebble deposit shaped like an arrow below the lookout bell",
        "mystery": "whether the arrow warned of a real danger or pointed toward hidden loot",
        "risk": "Rain had loosened stones above it, so the children stayed beneath the lookout roof with an adult.",
        "false": "The crew first read the arrow backward and searched toward the crowded dock.",
        "clue": "matching pebbles beside a drainage grate and chalk dust on the harbor keeper's glove",
        "cause": "The harbor keeper had arranged the deposit as a temporary arrow toward a blocked drain, then rain erased the label.",
        "action": "The children asked before acting, shared chalk, and made a new sign while adults secured the loose stones and grate.",
        "result": "The warning became clear, and visitors used the dry stairway until repairs were finished.",
        "lesson": "A sign is useful only when its meaning is confirmed.",
        "image": "When the clouds parted, the new white arrow shone beside three rain puddles reflecting the lookout bell.",
    },
    {
        "find": "a soft mud deposit covering half of a painted animal footprint trail",
        "mystery": "why the clinic's playful walking game ended at the steepest bend",
        "risk": "The crew did not step onto the covered trail; they investigated from the handrailed deck.",
        "false": "A deep mark convinced them for a moment that a giant seabird had landed there.",
        "clue": "a torn sandbag, a fan of grit, and the same paint color continuing beyond the muddy patch",
        "cause": "A torn erosion-control bag released a deposit of wet sand over the painted footprints.",
        "action": "The crew counted the missing prints for the groundskeeper and shared brushes to repaint them after adults replaced the bag and cleaned the deck.",
        "result": "Children at the pediatric clinic could follow the complete animal trail without nearing the slope.",
        "lesson": "Good repairs solve the hazard before restoring the decoration.",
        "image": "The final green turtle print dried under a paper awning, pointing safely toward the clinic door.",
    },
    {
        "find": "a dark deposit of soot beneath a tiny brass lantern fixed to a signpost",
        "mystery": "why the lantern kept dimming during the clinic's evening story hour",
        "risk": "The lantern was cold, but the crew still left its opening and fuel to an adult to inspect.",
        "false": "They briefly thought a shadow-loving sprite was swallowing the flame.",
        "clue": "a bent air vent, clean glass above it, and soot only on the sheltered side",
        "cause": "Wind-blown mud had bent the vent, so the smoky flame left a soot deposit beneath the lantern.",
        "action": "The crew shared mirrors to reflect daylight on the sign while the keeper replaced the damaged lantern with a sealed electric one.",
        "result": "The story-hour path glowed clearly without smoke or an open flame.",
        "lesson": "Magic is fun in a tale, but equipment needs a real inspection.",
        "image": "That evening, moths circled the cool electric light while a silver storybook waited on the dry bench.",
    },
    {
        "find": "a ribbon-like deposit of red sand winding from the ferry steps",
        "mystery": "why it stopped beside a pediatric supply wagon with one wheel raised",
        "risk": "The wagon was parked and chocked, and no child went below it or onto the wet incline.",
        "false": "Its bright color made the crew imagine a dragon had dragged its tail uphill.",
        "clue": "red grit inside the wheel tread, a matching patch on the ferry ramp, and an intact wagon seal",
        "cause": "The wheel had carried damp red sand from the ferry and deposited it each time it turned.",
        "action": "The crew photographed the trail, shared cones around it, and told the driver before an adult swept the grit into a sample tray.",
        "result": "The sealed pediatric supplies arrived safely, and the cleaned path no longer hid slippery mud.",
        "lesson": "A trail often records movement rather than mischief.",
        "image": "Four orange cones glowed in the sunset as the clean wagon rolled toward the clinic porch.",
    },
    {
        "find": "a waxy deposit on the rope rail beside a carved moon symbol",
        "mystery": "why the rope felt stiff and smelled faintly of lavender",
        "risk": "The crew tied a second safety line on level ground and did not depend on the stiff section.",
        "false": "The moon carving suggested that an old spell had frozen the rope.",
        "clue": "purple candle crumbs, a sheltered picnic ledge, and wax only beneath the overhang",
        "cause": "A lantern-making class had spilled warm candle wax, which cooled into a deposit on the rope.",
        "action": "The pediatrician kept the clinic group on the upper path while the crew reported the spot and adults replaced the affected rope.",
        "result": "The rail was dependable again, and the class added trays beneath every candle project.",
        "lesson": "A magical-looking clue may have an ordinary history.",
        "image": "A new rope curved above the slope, and the rescued moon carving hung inside the craft room beside a lavender candle.",
    },
    {
        "find": "a chalky deposit around the clinic's outdoor drinking fountain",
        "mystery": "why the fountain coughed and sent only a thin arc of water",
        "risk": "A clinician closed the fountain until its water quality and slippery puddle could be checked.",
        "false": "The crew first blamed a tiny shell wedged in the nozzle.",
        "clue": "white rings around several holes, a normal test at the indoor tap, and no shell at all",
        "cause": "Hard water slowly left a mineral deposit that narrowed the fountain openings.",
        "action": "The crew shared cups from the approved indoor station while the facilities worker serviced and tested the fountain.",
        "result": "After the worker declared it ready, the fountain made a smooth arc and the puddle was dried.",
        "lesson": "Health equipment should return to use only after a qualified adult checks it.",
        "image": "A clear ribbon of water sparkled above the basin, with a fresh inspection tag fluttering below it.",
    },
    {
        "find": "a deposit of silver fish scales beside a torn parcel label",
        "mystery": "whether an animal had opened the pediatric clinic's delivery",
        "risk": "The crew left the scales where they were and kept the muddy delivery bend clear.",
        "false": "A feather nearby made everyone picture a gull stealing medicine.",
        "clue": "an empty fish basket, an unbroken clinic parcel seal, and scale marks ending at the market cart",
        "cause": "A fishmonger's basket tipped during the rain; the clinic parcel merely shared the same cart.",
        "action": "The crew separated the two labels, shared a dry tarp, and helped the adults account for every sealed clinic box.",
        "result": "The delivery was complete, the market basket was returned, and no animal was wrongly blamed.",
        "lesson": "Nearby clues may belong to different stories.",
        "image": "Under the porch lamp, the last silver scale rested in a sample envelope beside the untorn clinic seal.",
    },
    {
        "find": "a glowing deposit of harmless moon-moss inside a stone compass rose",
        "mystery": "why it lit only one route across the muddy slope after dark",
        "risk": "The crew waited until the harbor keeper closed the steep paths, then joined the keeper on the handrailed route with a lantern.",
        "false": "They hoped the glow marked a buried pirate crown.",
        "clue": "dry boot prints on the lit route, rain pools on the others, and moss brightest beside drainage stones",
        "cause": "The old compass charm awakened the moon-moss to mark the one path that remained firm after rain.",
        "action": "The crew shared lanterns, watched the adult keeper test each firm stone, and posted the safe route for families leaving the pediatric clinic.",
        "result": "Everyone crossed together, and the other paths stayed closed until daylight repairs.",
        "lesson": "Even helpful magic works best with careful checking and shared responsibility.",
        "image": "The moon-moss faded at dawn, leaving twelve green stars beside a row of dry boot prints.",
    },
]

OPENINGS = [
    "The rain had just stopped when",
    "During the harbor's quietest morning watch,",
    "One windy afternoon,",
    "As clinic families boarded the ferry,",
    "Just before the lookout bell rang,",
    "After a night of silver rain,",
    "While gulls called above the dock,",
    "On the crew's careful map-making day,",
]

CLUE_LEADS = [
    "Instead of guessing again, they made a clue list:",
    '"Facts first," said {helper}, and everyone studied',
    "Their mystery board held the evidence that mattered:",
    "A second look changed the shape of the mystery. They noticed",
    "They compared what was near, what was missing, and",
    '"What can we actually prove?" asked {hero}. Together they found',
    "From the firm walkway, they sketched",
    "They numbered each observation and circled",
]

RESPONSE_LEADS = [
    "Once the clues agreed,",
    "With the false lead crossed out,",
    "After explaining the evidence to the harbor keeper,",
    "Nobody rushed. Instead,",
    "The answer suggested a practical next step, so",
    '"Now we know what happened," said {hero}. Then',
    "After assigning the safe jobs fairly,",
    "Their solution used no daring leap or slippery shortcut:",
]

REFLECTIONS = [
    "The mystery had become a useful answer, not a frightening rumor.",
    "They had solved more than a puzzle; they had made the route safer.",
    "The crew drew the cause and effect in the logbook so nobody would forget.",
    "Their best discovery was that patience could be braver than a scramble.",
    "Each crew member had supplied one piece of the answer.",
    "The well-supported explanation felt as satisfying as buried treasure.",
    "Their shared evidence had turned a muddle into a plan.",
    "They celebrated quietly, because a well-solved mystery leaves room to notice the ending.",
]

MAGIC_ASIDES = [
    "The compass charm winked once, but its magic could not replace evidence or identify an unknown substance.",
    "A green spark skipped over the compass charm; even in a magical tale, the crew still needed facts.",
    "The old compass charm hummed with quiet magic, offering encouragement rather than an answer.",
    "For one bright second the compass charm's magic pointed three ways, as if asking them to compare the clues.",
    "A thread of harmless magic lit the edge of their clue list, while the real explanation came from observation.",
    "The compass charm made a hopeful chime, but nobody treated magic as a safety test.",
    "Tiny stars of magic crossed the compass charm and faded; the crew kept working from what they could prove.",
    "Their compass charm glowed with magic beside the evidence, making the careful investigation feel like a true pirate quest.",
]

PEDIATRIC_EXPLANATION = (
    "Pediatric means relating to children's health or medical care; it is not the name of an illness."
)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: muddy slope, mystery, sharing, magic.")
    ap.add_argument("--name")
    ap.add_argument("--crew-name")
    ap.add_argument("--helper-name")
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
    name = args.name or rng.choice(NAMES)
    crew_name = args.crew_name or rng.choice(CREW)
    helper_name = args.helper_name or rng.choice(HELPERS)
    return StoryParams(
        name=name,
        crew_name=crew_name,
        helper_name=helper_name,
        incident_id=rng.randrange(len(INCIDENTS)),
        telling_mode=rng.randrange(len(OPENINGS)),
        clue_mode=rng.randrange(len(CLUE_LEADS)),
        response_mode=rng.randrange(len(RESPONSE_LEADS)),
        ending_mode=rng.randrange(len(REFLECTIONS)),
    )


def _build_world(params: StoryParams) -> World:
    world = World(SETTING)
    incident = INCIDENTS[params.incident_id % len(INCIDENTS)]
    hero = world.add(Entity(id="hero", kind="character", type="boy-pirate", label=params.name))
    crew = world.add(Entity(id="crew", kind="character", type="pirate-crew", label=params.crew_name, plural=True))
    helper = world.add(Entity(id="helper", kind="character", type="clinician", label=params.helper_name))
    deposit = world.add(Entity(id="deposit", type="deposit", label=incident["find"]))
    evidence = world.add(Entity(id="evidence", type="clue-set", label=incident["clue"]))
    lantern = world.add(Entity(id="lantern", type="lantern", label="gold lantern"))
    charm = world.add(Entity(id="charm", type="charm", label="compass charm"))

    hero.memes["curious"] = 1
    crew.memes["hope"] = 1
    helper.memes["calm"] = 1
    deposit.meters["identified"] = 0
    deposit.meters["mystery"] = 1
    evidence.meters["observed"] = 1
    lantern.meters["light"] = 1
    charm.meters["magic"] = 1

    world.facts.update(
        hero=hero,
        crew=crew,
        helper=helper,
        helper_role=HELPER_ROLES.get(params.helper_name, "a pediatric clinician visiting the harbor"),
        deposit=deposit,
        evidence=evidence,
        lantern=lantern,
        charm=charm,
        incident=incident,
        params=params,
        mystery_solved=False,
        route_safe=False,
    )
    return world


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    crew: Entity = f["crew"]
    helper: Entity = f["helper"]
    deposit: Entity = f["deposit"]
    incident: dict[str, str] = f["incident"]
    params: StoryParams = f["params"]
    opening = OPENINGS[params.telling_mode % len(OPENINGS)]
    clue_lead = CLUE_LEADS[params.clue_mode % len(CLUE_LEADS)].format(
        hero=hero.label, helper=helper.label
    )
    response_lead = RESPONSE_LEADS[params.response_mode % len(RESPONSE_LEADS)].format(
        hero=hero.label, helper=helper.label
    )
    reflection = REFLECTIONS[params.ending_mode % len(REFLECTIONS)]

    world.say(f"{opening} {hero.label} and {crew.label}, a band of young pirates, reached the muddy slope beside the harbor.")
    world.say(f"There they found {deposit.label}.")
    world.say(f"They had a mystery to solve: {incident['mystery']}.")

    world.para()
    world.say(incident["risk"])
    world.say(incident["false"])
    world.say(f"Then {helper.label}, {f['helper_role']}, explained, \"{PEDIATRIC_EXPLANATION}\"")

    world.para()
    world.say(f"{clue_lead} {incident['clue']}.")
    world.say(MAGIC_ASIDES[params.telling_mode % len(MAGIC_ASIDES)])
    world.say(incident["cause"])
    world.say(f"{hero.label} checked the explanation against every clue before the crew accepted it.")

    world.para()
    action = incident["action"]
    action_clause = action[:1].lower() + action[1:]
    world.say(f"{response_lead} {action_clause}")
    world.say(incident["result"])
    world.say(f"{crew.label.capitalize()} wrote the lesson in their shared log: {incident['lesson']}")

    world.para()
    world.say(reflection)
    world.say(incident["image"])

    deposit.meters["identified"] = 1
    deposit.meters["mystery"] = 0
    crew.memes["teamwork"] = 1
    f["mystery_solved"] = True
    f["route_safe"] = True


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    return [
        f'Write a short pirate tale for a young child that takes place on {world.setting.place} and includes the word "deposit".',
        f"Tell a story where {world.facts['hero'].label} and {world.facts['crew'].label} safely solve why they found {incident['find']}.",
        "Write a gentle mystery involving accurate pediatric vocabulary, shared work, evidence, and a concrete ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    crew: Entity = f["crew"]
    helper: Entity = f["helper"]
    incident: dict[str, str] = f["incident"]
    return [
        QAItem(
            question=f"What deposit did {hero.label} and {crew.label} find?",
            answer=f"They found {incident['find']}.",
        ),
        QAItem(
            question="What wrong first idea did the crew reconsider?",
            answer=incident["false"],
        ),
        QAItem(
            question=f"What evidence helped {hero.label} solve the mystery?",
            answer=f"The useful evidence was {incident['clue']}.",
        ),
        QAItem(
            question="What caused the mysterious deposit?",
            answer=incident["cause"],
        ),
        QAItem(
            question=f"How did {crew.label} respond safely?",
            answer=incident["action"],
        ),
        QAItem(
            question=f"What did {helper.label}'s pediatric role mean?",
            answer=PEDIATRIC_EXPLANATION,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a deposit?",
            answer="A deposit is something placed or left somewhere, like a kept token or a sum put in a safe place.",
        ),
        QAItem(
            question="What does pediatric mean?",
            answer=PEDIATRIC_EXPLANATION,
        ),
        QAItem(
            question="Why do people share tools?",
            answer="People share tools so everyone can help, and so one person does not have to do all the work alone.",
        ),
        QAItem(
            question="Why do stories use magic?",
            answer="Magic can make a story wonder-filled and help characters discover things they could not see before.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% This world is small and deterministic; the ASP twin only checks a few
% reasonableness relations.
mystery_needed :- deposit(glow), deposit(mystery).
sharing_needed :- crew(shared,tools).
magic_needed :- charm(magic).
good_story :- mystery_needed, sharing_needed, magic_needed.
#show good_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("deposit", "glow"),
        asp.fact("deposit", "mystery"),
        asp.fact("crew", "shared", "tools"),
        asp.fact("charm", "magic"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/0."))
    ok = any(sym.name == "good_story" for sym in model)
    if ok:
        print("OK: ASP twin agrees the story has mystery, sharing, and magic.")
        return 0
    print("MISMATCH: ASP twin did not find a good_story.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    tell(world)
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


CURATED = [
    StoryParams(name="Finn", crew_name="the little crew", helper_name="Dr. Marina"),
    StoryParams(name="Mira", crew_name="the salty crew", helper_name="Nurse Nell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_story/0."))
        print("good_story" if any(sym.name == "good_story" for sym in model) else "(none)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} on the muddy slope"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
