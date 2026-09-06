#!/usr/bin/env python3
"""
storyworlds/worlds/ghetto_chowder_repetition_happy_ending_ghost_story.py
========================================================================

A small story world about a child, a friendly ghost, a pot of chowder,
repeated clues, and a happy ending in a neighborhood community kitchen.

Seed tale inspiration:
---
On a chilly evening in the old neighborhood, a child hears a ghost whisper
the same two words again and again: "chowder, chowder." The ghost is not
trying to scare anyone. It is trying to remember a lost pot of chowder that
was promised to the building's neighbors. The child follows the repeating
voice, finds the missing pot, and shares the soup. The ghost finally smiles,
the repeating words stop, and the block feels warm and safe again.
"""

from __future__ import annotations

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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    container: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old block courtyard"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    ghost_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    id: str
    occasion: str
    repeated_clue: str
    obstacle: str
    first_guess: str
    evidence: str
    action: str
    truth: str
    repair: str
    lesson: str
    ending: str


NAMES = {
    "girl": ["Maya", "Nina", "Lena", "Ava", "Zuri", "Ivy"],
    "boy": ["Owen", "Theo", "Malik", "Eli", "Noah", "Jace"],
}
PARENTS = ["mother", "father", "grandmother", "grandfather"]
GHOST_NAMES = ["Moss", "Bells", "Milo", "Penny", "Soot", "Rue"]


INCIDENTS = [
    Incident(
        id="blue_door",
        occasion="the neighbors were preparing a welcome supper for a new family",
        repeated_clue="blue door, chowder",
        obstacle="the chowder pot had vanished before anyone could fill the bowls",
        first_guess="that a gust had rolled the pot behind the pantry shelves",
        evidence="a trail of dried bay leaves ended at the blue cupboard in the history room",
        action="matched the leaves to the recipe card and asked an adult to unlock the cupboard",
        truth="the cook had stored the pot there during a fire drill and forgotten to leave a note",
        repair="carried the covered pot back on a sturdy cart and set out bowls for every guest",
        lesson="good clues deserve a careful check before anyone is blamed",
        ending="blue bowls circled the table while steam drew silver curls above them",
    ),
    Incident(
        id="bell_rope",
        occasion="a winter wind rattled the windows during the block's lantern walk",
        repeated_clue="bell, then chowder",
        obstacle="the supper bell rang, but the kitchen serving hatch would not open",
        first_guess="that the old ghost had tied the hatch shut as a joke",
        evidence="each tug of the bell rope made a loose wooden peg tap beneath the counter",
        action="listened between the clangs, found the fallen latch peg, and fetched the caretaker",
        truth="the peg had slipped into the track and jammed the hatch",
        repair="held a lamp while the caretaker reset the peg and tested the hatch twice",
        lesson="repeated sounds can be useful evidence when people stop and listen",
        ending="lantern stars shone through the open hatch onto a neat row of chowder cups",
    ),
    Incident(
        id="cold_pot",
        occasion="the community kitchen was opening after a snowy afternoon",
        repeated_clue="cold chowder, wait",
        obstacle="the pot was on the stove, yet its safety thermometer showed that it was still cold",
        first_guess="that the thermometer was broken because the lid felt warm",
        evidence="a second clean thermometer gave the same reading and the burner light was dark",
        action="kept everyone from tasting the soup and asked the cook to inspect the stove",
        truth="a tripped safety switch had turned the burner off",
        repair="waited while the cook reset the switch and reheated the chowder to a safe temperature",
        lesson="patient checking matters more than rushing toward a treat",
        ending="snow tapped the glass as safely warmed bowls brightened the long table",
    ),
    Incident(
        id="recipe_pages",
        occasion="families were gathering to copy recipes for the neighborhood archive",
        repeated_clue="page three, chowder",
        obstacle="the chowder recipe ended halfway through and nobody knew the final steps",
        first_guess="that the ghost wanted them to invent whatever ingredients they liked",
        evidence="three pale flour marks crossed the floor toward a display case of old notebooks",
        action="followed the marks, compared page numbers, and asked the archivist to open the case",
        truth="page three had been filed with a photograph after the pages stuck together",
        repair="returned the page, copied the complete recipe, and marked every common allergen clearly",
        lesson="records become useful when they are complete and shared responsibly",
        ending="the restored recipe dried beside a bowl painted with tiny white boats",
    ),
    Incident(
        id="steam_window",
        occasion="the block was rehearsing songs for its spring supper",
        repeated_clue="wipe, read, chowder",
        obstacle="the ghost's message appeared backward in steam on the kitchen window",
        first_guess="that the swirls were only random marks from the damp air",
        evidence="wiping one corner revealed an arrow that returned after the next puff of steam",
        action="held paper to the glass, copied the marks in reverse, and read the hidden direction",
        truth="the message pointed to a covered vegetarian chowder cooling on the safe pantry shelf",
        repair="asked the cook to label both chowders and place them at separate serving stations",
        lesson="a puzzling message can become clear when it is viewed another way",
        ending="two labeled ladles gleamed beneath a window cleared to the evening sky",
    ),
    Incident(
        id="roof_leak",
        occasion="rain began during a rooftop-garden harvest supper",
        repeated_clue="drip, move the chowder",
        obstacle="water started dripping from the ceiling near the serving table",
        first_guess="that the ghost was making rain indoors to get attention",
        evidence="every drip landed beneath a dark seam that led toward a loose roof drain cover",
        action="moved people and food away from the wet area and called the building manager",
        truth="leaves had blocked the roof drain and backed water over the flashing",
        repair="helped set up supper in the dry hall while trained adults cleared the drain",
        lesson="the safest first step is often to protect people before solving the mystery",
        ending="rainwater ticked into a bucket while neighbors ate together under paper sunflowers",
    ),
    Incident(
        id="missing_ladle",
        occasion="the youngest children were setting places for a story-night supper",
        repeated_clue="count the ladles, chowder",
        obstacle="one serving station had no ladle and its line could not move",
        first_guess="that someone had selfishly taken the shiny utensil home",
        evidence="round drops crossed the clean floor toward a box of puppet-stage props",
        action="counted every utensil, followed the drops, and checked the prop box with the teacher",
        truth="a helper had mistaken the ladle for the moon in a puppet show",
        repair="washed and sanitized the ladle, then made a cardboard moon for the show",
        lesson="asking what happened is kinder and wiser than making an accusation",
        ending="a paper moon rose over the puppets as the real ladle rested beside the chowder",
    ),
    Incident(
        id="faded_labels",
        occasion="the kitchen volunteers were arranging a choose-your-own-toppings supper",
        repeated_clue="labels first, chowder second",
        obstacle="steam had blurred the labels on three covered topping bowls",
        first_guess="that everyone could identify the toppings by smell alone",
        evidence="one volunteer's written checklist still listed each bowl by its colored handle",
        action="closed the serving line, compared handle colors, and confirmed the list with the cook",
        truth="the lids had been switched while the bowls were being washed",
        repair="restored the lids and made large fresh labels before service resumed",
        lesson="clear labels help people make safe and comfortable choices",
        ending="green, red, and gold cards stood crisp beside the gently bubbling pot",
    ),
    Incident(
        id="power_outage",
        occasion="a thunderstorm darkened the block just before supper",
        repeated_clue="do not open, save the chowder",
        obstacle="the power failed while chilled chowder waited in the refrigerator",
        first_guess="that opening the door often would prove whether the food was still cold",
        evidence="the ghost pointed to the refrigerator thermometer and covered the handle with both hands",
        action="left the door shut, read the emergency card, and asked an adult to note the outage time",
        truth="the closed refrigerator could keep the food cold while the crew checked the safety plan",
        repair="served shelf-stable snacks first and used the chowder only after the cook confirmed it was safe",
        lesson="a calm plan can protect a celebration when the lights go out",
        ending="battery lanterns made warm circles while thunder faded beyond the courtyard",
    ),
    Incident(
        id="wrong_address",
        occasion="neighbors were packing supper for an elder who could not come downstairs",
        repeated_clue="fourteen, not forty, chowder",
        obstacle="the delivery card seemed to send the chowder to an empty apartment",
        first_guess="that the elder had moved without telling anyone",
        evidence="the ghost traced a small one beside the large four on an old handwritten card",
        action="checked the current resident list with the coordinator and called upstairs before leaving",
        truth="a faded numeral made apartment fourteen look like apartment forty",
        repair="wrote a clear new card and delivered the sealed bowl to the correct door with an adult",
        lesson="confirming a detail can prevent a small mark from becoming a large mistake",
        ending="a porch light blinked thanks as the empty cart rolled softly home",
    ),
    Incident(
        id="memory_table",
        occasion="the block was holding a supper to remember neighbors from long ago",
        repeated_clue="one bowl for Alma, chowder",
        obstacle="nobody knew why the ghost kept asking for a bowl bearing an unfamiliar name",
        first_guess="that Alma must be another ghost waiting in the cellar",
        evidence="a faded group photograph showed Alma serving soup from the same copper pot",
        action="read the photograph's caption aloud and invited the oldest neighbor to tell Alma's story",
        truth="Alma had started the shared supper tradition many years earlier",
        repair="placed an empty commemorative bowl beside the photograph and served the living guests",
        lesson="remembering a generous person can help a community continue their kindness",
        ending="the copper pot reflected Alma's photograph and every smiling face around it",
    ),
    Incident(
        id="garden_herbs",
        occasion="children had harvested herbs for the last courtyard supper of summer",
        repeated_clue="not that leaf, chowder",
        obstacle="two baskets of green leaves had been placed beside the cooking table",
        first_guess="that every fragrant courtyard leaf must be safe to stir into soup",
        evidence="the garden map marked one basket as edible herbs and the other as leaves for a craft",
        action="kept both baskets away from the pot and asked the garden leader to identify them",
        truth="the craft leaves were not food and had been carried to the wrong table",
        repair="returned the craft leaves, washed the approved herbs, and let the cook add them",
        lesson="unknown plants should never be tasted without a knowledgeable adult's approval",
        ending="safe green herbs flecked the chowder while leaf prints fluttered on a nearby clothesline",
    ),
]

OPENINGS = [
    "A friendly ghost mystery began when",
    "The old building had been quiet all afternoon, but that changed when",
    "No one expected a pale visitor on the evening when",
    "A soft spoon-shaped glow appeared just as",
    "The neighborhood's gentlest mystery arrived while",
    "A floorboard creaked three times on the night when",
    "The courtyard clock had barely chimed when",
    "Warm kitchen smells filled the hall as",
]

THINKING_LINES = [
    '"A repeated clue is trying to point somewhere," {child} said.',
    '"Let us test one idea at a time," {child} suggested.',
    '"We know what we saw, but not what caused it," {child} reminded everyone.',
    '"Before we guess about anyone, we should gather evidence," {child} said.',
    '"Maybe the words matter in the order {ghost} says them," {child} wondered.',
    '"The ghost sounds urgent, not unkind," {child} told {parent}.',
    '"What changes each time the clue repeats?" {child} asked.',
    '"There must be a safe way to check," {child} said.',
]

HISTORY_LINES = [
    "In the history room, a plaque quoted an old city record that used the word 'ghetto.' It explained that this is a historically loaded word tied to forced separation and hardship, not a casual name for people or a neighborhood today.",
    "An archive label included the old word 'ghetto' because it appeared in a historical record. The label carefully explained its painful connection to segregation and warned visitors not to use it loosely about people or places.",
    "A local-history display preserved the word 'ghetto' inside a quotation from the past. Beside it, a note explained that the term carries a history of confinement and discrimination and should be handled with care.",
    "The community archive showed the old word 'ghetto' only in its historical context. A curator's note described its association with enforced separation and made clear that it was not a nickname for anyone there.",
]


def _repeat(world: World, speaker: Entity, words: str, times: int = 3) -> None:
    speaker.memes["repetition"] = speaker.memes.get("repetition", 0.0) + times
    world.say(f'{speaker.id} repeated, "{words}. {words}."')


def tell_story(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    incident = INCIDENTS[rng.randrange(len(INCIDENTS))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))]
    thinking = THINKING_LINES[rng.randrange(len(THINKING_LINES))]
    history = HISTORY_LINES[rng.randrange(len(HISTORY_LINES))]
    world = World(Setting(place="the old block's community courtyard"))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent.capitalize(), kind="character", type=params.parent))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost"))
    pot = world.add(Entity(id="pot", type="pot", label="pot of chowder", phrase="a big pot of chowder"))
    clue = world.add(Entity(id="clue", type="evidence", label=incident.evidence, phrase=incident.evidence))

    world.say(
        f"{opening} {incident.occasion}. {child.id} and {parent.id} were helping in "
        f"{world.setting.place} when {ghost.id}, a small friendly ghost, drifted into view."
    )
    world.say(history)
    world.say(f"Then they discovered that {incident.obstacle}.")
    _repeat(world, ghost, incident.repeated_clue, 2)

    world.para()
    world.say(
        f"At first, {child.id} guessed {incident.first_guess}. {parent.id} agreed that it was "
        f"only a guess, so nobody accused or frightened anyone."
    )
    world.say(thinking.format(child=child.id, ghost=ghost.id, parent=parent.id))
    ghost.memes["sad"] = 1.0
    world.say(
        f"Instead of trying to scare them, {ghost.id} pointed out this evidence: {incident.evidence}. "
        f'Then the ghost whispered, "{incident.repeated_clue}," once more.'
    )

    world.para()
    world.say(
        f"With {parent.id} beside them, {child.id} {incident.action}. The clues finally showed the "
        f"truth: {incident.truth}."
    )
    world.say(
        f'"Now the repeated words make sense," {child.id} said. "They helped us notice what mattered."'
    )
    world.say(f"Together, the neighbors {incident.repair}.")

    world.para()
    ghost.memes["sad"] = 0.0
    ghost.memes["joy"] = 1.0
    child.memes["joy"] = 1.0
    child.memes["careful_reasoning"] = 1.0
    pot.meters["shared_safely"] = 1.0
    clue.meters["understood"] = 1.0
    world.say(
        f"The chowder supper ended happily. {ghost.id} smiled, and {child.id} understood that "
        f"{incident.lesson}."
    )
    world.say(
        f"The ghost said 'chowder' one final time, now as a cheerful toast. At the end of the night, "
        f"{incident.ending}."
    )

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        pot=pot,
        clue=clue,
        incident=incident,
        place=world.setting.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    incident: Incident = f["incident"]
    return [
        f"Write a gentle ghost story for a young child in which {child.id} solves the {incident.id.replace('_', ' ')} mystery by following a repeated chowder clue.",
        f"Tell a cozy community-kitchen story about {incident.obstacle}, careful investigation, and a happy ending.",
        f"Write a child-safe neighborhood ghost story where repetition helps reveal that {incident.truth}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    ghost: Entity = f["ghost"]
    incident: Incident = f["incident"]
    return [
        QAItem(
            question=f"What problem did {child.id} and {parent.id} notice?",
            answer=f"They noticed that {incident.obstacle}. It happened while {incident.occasion}.",
        ),
        QAItem(
            question=f"What clue did {ghost.id} repeat?",
            answer=f'{ghost.id} repeated "{incident.repeated_clue}." The repetition directed attention to useful evidence.',
        ),
        QAItem(
            question=f"What evidence helped solve the {incident.id.replace('_', ' ')} mystery?",
            answer=f"The useful evidence was that {incident.evidence}. It helped show that {incident.truth}.",
        ),
        QAItem(
            question=f"How did the neighbors repair the problem?",
            answer=f"The neighbors {incident.repair}. They acted on the evidence instead of the first guess.",
        ),
        QAItem(
            question=f"What did {child.id} learn before the happy ending?",
            answer=f"{child.id} learned that {incident.lesson}. The final image showed that {incident.ending}.",
        ),
        QAItem(
            question="Why did the story mention the historical word 'ghetto'?",
            answer="It appeared only in a quotation or archive explanation about the past. The story explains that the word is historically loaded and should not be used casually for people or neighborhoods.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chowder?",
            answer="Chowder is a thick soup, often made with milk or cream, potatoes, and vegetables or fish.",
        ),
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means saying or doing the same thing more than once, which can make a story feel rhythmic or important.",
        ),
        QAItem(
            question="Why can a ghost story still be gentle?",
            answer="A ghost story can be gentle when the ghost is friendly, the problem is small, and the ending feels safe and warm.",
        ),
        QAItem(
            question="Why is the word 'ghetto' handled carefully?",
            answer="The word has a painful history connected to forced separation, confinement, and discrimination. Historical sources may contain it, but it should not be applied casually to people or places.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% The ghost repeats the food word when it is sad and the chowder is hidden.
needs_reassurance(G) :- ghost(G), sad(G).
repeats_chowder(G) :- needs_reassurance(G), hidden(chowder_pot).

% A happy ending happens when the child finds the pot and shares the soup.
happy_ending :- found(chowder_pot), shared(chowder_pot).

#show needs_reassurance/1.
#show repeats_chowder/1.
#show happy_ending/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("ghost", "moss"),
        asp.fact("sad", "moss"),
        asp.fact("hidden", "chowder_pot"),
        asp.fact("found", "chowder_pot"),
        asp.fact("shared", "chowder_pot"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0."))
    happy = bool(asp.atoms(model, "happy_ending"))
    if happy:
        print("OK: ASP reasoning confirms the happy ending.")
        return 0
    print("MISMATCH: ASP reasoning did not confirm the happy ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with repetition and a happy ending.")
    ap.add_argument("--name", choices=sorted({n for vals in NAMES.values() for n in vals}))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    inferred_gender = next(
        (gender for gender, names in NAMES.items() if args.name in names),
        None,
    )
    gender = args.gender or inferred_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENTS)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(name=name, gender=gender, parent=parent, ghost_name=ghost_name)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.container:
            bits.append(f"container={e.container}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(name="Maya", gender="girl", parent="mother", ghost_name="Moss", seed=4101),
    StoryParams(name="Owen", gender="boy", parent="father", ghost_name="Bells", seed=4102),
    StoryParams(name="Nina", gender="girl", parent="grandmother", ghost_name="Rue", seed=4103),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show needs_reassurance/1. #show repeats_chowder/1. #show happy_ending/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1

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
