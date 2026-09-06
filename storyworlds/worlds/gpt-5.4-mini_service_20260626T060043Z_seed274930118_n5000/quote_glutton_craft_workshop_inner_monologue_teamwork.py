#!/usr/bin/env python3
"""
A standalone Storyweavers world: a small whodunit set in a craft workshop.

Premise:
- In a cozy craft workshop, a prized quote card disappears during a busy afternoon.
- A gluttonous squirrel-like helper keeps sneaking snacks from the supply table.
- The hero's inner monologue helps them notice clues.
- Teamwork solves the mystery and restores the missing quote.

This script follows the Storyworld contract:
- standalone stdlib Python
- lazy ASP import for verification/query modes
- world simulation with physical meters and emotional memes
- StorySample/QAItem/StoryError from storyworlds.results
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

THEME = "craft workshop"
SEED_WORDS = {"quote", "glutton"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["lost", "sticky", "crumbs", "ink", "dust"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "joy", "curiosity", "doubt", "teamwork", "pride", "hunger"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str = "Mina"
    sidekick: str = "Toby"
    culprit: str = "Chipper"
    case: int = 0
    telling_mode: int = 0
    thought_style: int = 0
    ending_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    project: str
    trouble: str
    snack: str
    first_clue: str
    false_lead: str
    thought: str
    split_search: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending: str


CASES = [
    Case(
        project="a banner of paper constellations",
        trouble="the quote card vanished just as the ceiling fan scattered silver stars",
        snack="a blueberry muffin",
        first_clue="a blue crumb beside the fan switch and a curl of silver paper under the ribbon roller",
        false_lead="an open window suggested that the card had blown outside",
        thought="Wind can carry paper, but that silver curl points toward the roller.",
        split_search="check the window ledge while the other traced the ribbon scraps",
        discovery="rolled the ribbon spool backward and eased the quote card from its wooden axle",
        cause="had reached for the muffin, bumped the fan switch, and chased the card when the gust swept it away",
        repair="unplugged the fan, flattened the card beneath a clean cutting mat, and finished the banner together",
        proof="the fan was off, the ribbon rolled smoothly, and every silver star stayed in place",
        lesson="A strong clue explains the whole chain of events, not merely the last thing that moved.",
        ending="Above the quiet fan, the restored quote card shone at the center of a paper night sky.",
    ),
    Case(
        project="felt badges for the workshop helpers",
        trouble="the quote card disappeared while everyone carried armfuls of felt to the sewing corner",
        snack="a cinnamon bun",
        first_clue="a thread from the card's red tassel caught on an apron pocket",
        false_lead="a lumpy cushion looked exactly large enough to hide a card",
        thought="The cushion is lumpy, but only the apron carries the quote's red thread.",
        split_search="sort the cushions while the other followed the snagged thread",
        discovery="found the quote card folded safely inside the spare apron pocket",
        cause="had tucked away the bun to free both paws, then scooped up the card with the apron by mistake",
        repair="brushed away the cinnamon, pressed the fold flat, and stitched a bright card pocket onto the notice board",
        proof="the new pocket held firm even when they carried the finished badges past it",
        lesson="Teamwork improves when each searcher follows different evidence and then compares what they learned.",
        ending="The final felt badge read HELPER, and the quote peeked neatly from its new red pocket.",
    ),
    Case(
        project="a glittering cardboard castle",
        trouble="the quote card was missing after a tray of glitter tipped with a whispery hiss",
        snack="two jam crackers",
        first_clue="three square clean marks on the glitter tray and one sticky corner beneath it",
        false_lead="sparkling pawprints seemed to march toward the supply cupboard",
        thought="Those prints leave the tray, but the clean squares show what rested underneath it.",
        split_search="inspect the cupboard while the other lifted each tray carefully",
        discovery="peeled the quote card from the underside of the glitter tray without tearing it",
        cause="had steadied the wobbling tray after taking a cracker, unknowingly pressing it onto the sticky card",
        repair="used waxed paper to free the corner, swept the glitter, and built the castle's towers as a team",
        proof="the cleaned tray sat level and the rescued card had no new tear",
        lesson="A person can cause a problem by accident and still take honest responsibility for repairing it.",
        ending="One last speck of gold glitter winked beside the quote like a tiny castle lantern.",
    ),
    Case(
        project="printed invitations for family craft night",
        trouble="the quote card disappeared when the hand press gave an unexpected clunk",
        snack="a cheese twist",
        first_clue="backward letters faintly stamped on scrap paper inside the press",
        false_lead="an empty card rack made it seem that somebody had carried the quote away",
        thought="A missing card cannot print letters unless it passed through the press.",
        split_search="count the card rack while the other opened the press with the safety latch",
        discovery="found the quote card pressed between two sheets of practice paper",
        cause="had leaned on the handle while reaching past it for the cheese twist",
        repair="released the press, replaced the bent handle pin, and reprinted the smudged invitations together",
        proof="the repaired press made one crisp invitation without catching any extra paper",
        lesson="Careful work means stopping the machine before reaching across it.",
        ending="The last invitation dried beneath the quote, both showing sharp black letters in the lamplight.",
    ),
    Case(
        project="care parcels for the children's library",
        trouble="the quote card vanished during a muddle of boxes, tissue paper, and snack wrappers",
        snack="a honey oat bar",
        first_clue="a corner of cream card visible through the handle slot of a sealed parcel",
        false_lead="the recycling basket held paper the same color as the quote",
        thought="Matching color is weak evidence; that square corner has the quote's blue border.",
        split_search="sort the recycling while the other compared every parcel's handle slot",
        discovery="opened the library parcel and found the quote card cushioning a jar of paper stars",
        cause="had swept the card into the box while gathering crumbs and wrappers in a hurry",
        repair="repacked the jar with proper padding, resealed the parcel, and made a labeled tray for loose cards",
        proof="a gentle shake produced no rattle, and the quote remained in its labeled tray",
        lesson="Tidying quickly is not the same as sorting carefully.",
        ending="By the door, the parcel waited under a tidy quote card and a bow shaped like an open book.",
    ),
    Case(
        project="a woven yarn rainbow",
        trouble="the quote card disappeared after a basket of yarn rolled across the floor",
        snack="a sesame biscuit",
        first_clue="a stiff rectangle making the violet yarn bulge in one place",
        false_lead="a trail of crumbs ended beneath the weaving table",
        thought="The crumbs show where the snack went, but the yarn's shape shows where the card went.",
        split_search="look beneath the table while the other unwound the violet yarn without cutting it",
        discovery="slid the quote card from the center of the tangled yarn ball",
        cause="had dived after the rolling biscuit and knocked the open basket into the card stand",
        repair="held the skeins while the two children rewound them by color and completed the rainbow",
        proof="each skein rested in its own cubby and the rainbow hung without a knot",
        lesson="The most tempting clue is not always the clue that explains the missing object.",
        ending="Violet yarn framed the rescued quote while seven soft colors curved above it.",
    ),
    Case(
        project="clay tiles for a garden path",
        trouble="the quote card vanished beside a row of freshly rolled clay slabs",
        snack="an apple turnover",
        first_clue="a shallow rectangle and reversed letters impressed in the last clay slab",
        false_lead="muddy tracks led toward the wash basin",
        thought="Tracks tell me who walked away; reversed letters tell me what touched the clay.",
        split_search="follow the tracks while the other lifted the clay with a wide wooden board",
        discovery="uncovered the quote card beneath the slab, damp but whole",
        cause="had set down the turnover, tried to wipe the table, and pushed soft clay over the card",
        repair="blotted the card, remixed the clay, and stamped a new teamwork tile together",
        proof="the new tile carried three clear handprints without trapping anything beneath it",
        lesson="Good detectives separate evidence about a person from evidence about what happened.",
        ending="At sunset, the teamwork tile dried beside the quote, its three handprints glowing warm red.",
    ),
    Case(
        project="shadow puppets for a tiny stage",
        trouble="the quote card disappeared when the stage curtain sagged during rehearsal",
        snack="a pocket of popcorn",
        first_clue="the quote's tassel dangling behind the cardboard moon",
        false_lead="a rustle inside the dragon puppet sounded as though paper were hidden there",
        thought="The dragon rustles, but the moon is wearing a tassel it did not have before.",
        split_search="inspect the puppets while the other lowered the moon's support rod",
        discovery="freed the quote card, which had become wedged behind the moon scenery",
        cause="had tugged the curtain to catch falling popcorn and shaken the loose scenery",
        repair="tightened the curtain knot, swept the popcorn, and rehearsed the scene with assigned jobs",
        proof="the curtain rose twice, the moon stayed straight, and no prop wandered",
        lesson="A team is strongest when everyone knows the job they agreed to do.",
        ending="On the final bow, the quote cast a crisp little shadow beside the cardboard moon.",
    ),
    Case(
        project="pressed-flower bookmarks",
        trouble="the quote card disappeared among blossoms laid on the drying rack",
        snack="a lemon cookie",
        first_clue="a blue border showing between two sheets of blotting paper",
        false_lead="a lemony smudge marked the door of the paint cupboard",
        thought="The smudge explains a paw's path, but the straight blue line belongs to the quote.",
        split_search="clean the cupboard mark while the other checked the drying layers from the top down",
        discovery="lifted the blotters and found the quote card pressing a small yellow flower",
        cause="had used the nearest flat card to save a flower after the cookie plate bumped the rack",
        repair="moved the flower to a proper press, cleaned the card, and finished a bookmark for each helper",
        proof="the flower lay flat in its press and all three bookmarks dried on labeled shelves",
        lesson="Helping in a hurry works better when you ask which tools are safe to use.",
        ending="A yellow flower glowed through the last bookmark beneath the clean blue edge of the quote.",
    ),
    Case(
        project="costumes for a sock-puppet parade",
        trouble="the quote card vanished while buttons bounced from an overturned sorting tin",
        snack="a raisin scone",
        first_clue="one gold button stuck to a tacky patch on the quote's wooden stand",
        false_lead="a sock puppet had a suspicious square bulge in its striped hat",
        thought="The bulge may be stuffing; the stuck button proves the stand was knocked near the tin.",
        split_search="check the puppet costumes while the other followed the line of rolling buttons",
        discovery="found the quote card beneath the wheeled costume trunk",
        cause="had chased the last raisin, bumped the button tin, and pushed the trunk over the fallen card",
        repair="blocked the trunk's wheels, sorted every button by size, and sewed the loose costumes together",
        proof="the trunk stayed parked and each costume kept its buttons through a practice march",
        lesson="Fixing the cause of an accident matters as much as cleaning up what it scattered.",
        ending="The smallest puppet saluted the restored quote with a bright gold button over its heart.",
    ),
    Case(
        project="a window display of folded paper birds",
        trouble="the quote card disappeared after the display door began tapping in the breeze",
        snack="a slice of banana bread",
        first_clue="a blue paper edge caught beside the lower hinge",
        false_lead="one folded bird lay outside on the sill",
        thought="The bird reached the sill through the open door, but the blue edge is still caught at the hinge.",
        split_search="retrieve the paper bird while the other held the display door safely open",
        discovery="pulled the creased quote card from behind the loose hinge plate",
        cause="had opened the display for a better view while eating and forgotten to latch it",
        repair="tightened the hinge, added a simple latch, and refolded the wrinkled birds as a team",
        proof="a breeze fluttered outside, yet the latched display stayed quiet",
        lesson="Admitting a forgotten step lets a team repair the real problem.",
        ending="Behind the glass, twelve paper birds circled the quote without stirring in the wind.",
    ),
    Case(
        project="recycled-paper lanterns",
        trouble="the quote card vanished during cleanup before the lantern parade",
        snack="a carrot cupcake",
        first_clue="a blue corner tucked inside a roll of clean scrap paper",
        false_lead="frosting on the recycling-bin rim made the bin seem like the obvious answer",
        thought="The frosting shows where a paw rested, not where the card landed; that blue corner is stronger.",
        split_search="wash the bin rim while the other unrolled the clean-paper bundle",
        discovery="found the quote card wrapped inside the lantern paper",
        cause="had gathered scraps with frosting on one paw and rolled the loose quote up with them",
        repair="washed paws, sorted reusable paper from rubbish, and assembled the final lantern together",
        proof="three labeled bins stood clean and the lantern held its shape when lifted",
        lesson="Fair questions and clear evidence are kinder than turning a mistake into a name for someone.",
        ending="When the lights dimmed, the quote rested below a lantern glowing like a small orange moon.",
    ),
]


@dataclass
class World:
    hero: Entity
    sidekick: Entity
    culprit: Entity
    quote_card: Entity
    teacup: Entity
    craft_table: Entity
    note_board: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _new_entity(eid: str, kind: str, type_: str, label: str, phrase: str = "", **kwargs) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, phrase=phrase, **kwargs)


def build_world(params: StoryParams) -> World:
    hero = _new_entity(params.name, "character", "girl", "the maker", meters={}, memes={})
    sidekick = _new_entity(params.sidekick, "character", "boy", "the helper", meters={}, memes={})
    culprit = _new_entity(params.culprit, "character", "animal", "the glutton", meters={}, memes={})
    quote_card = _new_entity("quote_card", "thing", "card", "quote card", 'a neat card with a quote on it')
    teacup = _new_entity("teacup", "thing", "cup", "tea cup", "a tiny cup of tea")
    craft_table = _new_entity("table", "thing", "table", "craft table", "the long craft table")
    note_board = _new_entity("board", "thing", "board", "notice board", "the cork board by the window")
    world = World(
        hero=hero,
        sidekick=sidekick,
        culprit=culprit,
        quote_card=quote_card,
        teacup=teacup,
        craft_table=craft_table,
        note_board=note_board,
    )
    world.facts["theme"] = THEME
    return world


def _inner_monologue(world: World, hero: Entity, clue: str) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["doubt"] += 1
    world.say(f'{hero.id}\'s inner monologue sharpened: "{clue}"')


def _teamwork(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["teamwork"] += 1
    sidekick.memes["teamwork"] += 1
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, s, c = world.hero, world.sidekick, world.culprit
    q, t, table, board = world.quote_card, world.teacup, world.craft_table, world.note_board
    case = CASES[params.case % len(CASES)]

    h.memes["worry"] += 1
    s.memes["pride"] += 1
    c.memes["hunger"] += 2
    q.meters["lost"] = 1
    t.meters["crumbs"] = 1

    openings = [
        f"The {THEME} hummed with scissors and soft chatter while {h.id}, {s.id}, and {c.id}, a snack-loving squirrel, made {case.project}.",
        f"On a bright workshop afternoon, {h.id} led a project to make {case.project}; {s.id} organized the tools, and {c.id}, a squirrel helper, carried supplies.",
        f"Glue lids clicked and paper rustled in the {THEME}. At the busiest table, {h.id} and {s.id} were showing {c.id} how to make {case.project}.",
        f"Before visitors arrived, {h.id}'s team had one last job in the {THEME}: finish {case.project}. {s.id} checked the materials while {c.id} fetched them.",
        f"Half-finished work on {case.project} covered the long table when {h.id} called {s.id} and {c.id} over for the afternoon's final craft.",
        f"The day's teamwork challenge sounded simple: {h.id}, {s.id}, and {c.id} would complete {case.project} before cleanup.",
        f"In the {THEME}, {h.id} carefully laid out the pieces for {case.project}. {s.id} counted them, and {c.id} arrived carrying a snack.",
        f"Everything was ready for {case.project}, from the clean tools to the tiny {t.label}. {h.id} checked that the quote card still hung on the board.",
    ]
    trouble_lines = [
        f"Their plan stopped: {case.trouble}.",
        f"Then came the problem: {case.trouble}.",
        f"A moment later, {case.trouble}.",
        f"Before the next step could begin, {case.trouble}.",
    ]
    world.say(openings[params.telling_mode % len(openings)])
    world.say(trouble_lines[(params.telling_mode + params.thought_style) % len(trouble_lines)])
    world.say("The craft workshop's quote card carried a line about teamwork, so the empty spot mattered to everyone.")

    world.para()
    world.say(f"Near the table lay {case.first_clue}. Meanwhile, {case.false_lead}.")
    thoughts = [
        case.thought,
        f"Two clues can point in different directions. Which one could have touched the quote card? {case.thought}",
        f"I should explain the evidence before I guess. {case.thought}",
        f"Slow down, look at what changed, and test one idea at a time. {case.thought}",
    ]
    _inner_monologue(world, h, thoughts[params.thought_style % len(thoughts)])
    dialogue = [
        f"{s.id} said, 'Let's each follow one clue and meet back here.'",
        f"'No guessing about anyone,' {h.id} said. 'We follow the objects and compare notes.'",
        f"{c.id} set down {case.snack} and asked, 'Can I help search too?' 'Yes,' said {s.id}, 'with clean paws and a careful plan.'",
        f"'The first idea may be wrong,' {s.id} said. {h.id} nodded. 'That is why a team checks it.'",
    ]
    world.say(dialogue[(params.telling_mode + params.ending_style) % len(dialogue)])
    world.say(f"They agreed that one child would {case.split_search}.")

    world.para()
    search_turns = [
        f"The false lead explained one mark but not the missing card. When the searchers traded observations, the stronger clue finally made sense.",
        f"Their first search found nothing. Instead of blaming anyone, they laid both clues side by side and noticed which one matched the card.",
        f"One clue ended without an answer; the other connected the empty board to the worktable. Together, the team followed that chain.",
        f"Each helper reported exactly what they had seen. The reports ruled out the easy guess and left one testable place to look.",
        f"They paused after the first attempt, changed jobs, and checked the evidence from the opposite direction.",
        f"The room grew quiet except for careful footsteps. A small detail from each search joined into one useful answer.",
        f"{h.id} asked what the clue proved, not whom it accused. That question turned three scattered details into a path.",
        f"Nobody searched alone for long: every discovery was called out, checked, and added to the team's growing explanation.",
    ]
    world.say(search_turns[params.telling_mode % len(search_turns)])
    world.say(f"At last, {h.id} and {s.id} {case.discovery}.")
    q.meters["lost"] = 0
    q.carried_by = h.id
    c.memes["doubt"] += 1
    admissions = [
        f"{c.id}'s ears lowered. 'I remember now,' the squirrel said. 'I {case.cause}. I did not mean to hide it, but I should have told you what happened.'",
        f"Seeing the evidence, {c.id} spoke up: 'I can explain. I {case.cause}. It was an accident, and I want to help mend it.'",
        f"'That clue fits what I did,' {c.id} admitted. 'I {case.cause}. I was worried you would be cross, so I stayed quiet.'",
        f"{c.id} took a breath and explained, 'I {case.cause}. Thank you for asking before deciding it was deliberate.'",
    ]
    world.say(admissions[(params.thought_style + params.telling_mode) % len(admissions)])

    world.para()
    _teamwork(world, h, s)
    c.memes["teamwork"] += 1
    c.memes["pride"] += 1
    world.say(f"The three helpers {case.repair}.")
    world.say(f"They tested their work: {case.proof}.")
    label_lines = [
        f"On an old scrap, someone had written the word 'glutton.' {h.id} crossed it out. 'That word turns one hungry mistake into a hurtful name for a person. We can say what happened without naming anybody that way.'",
        f"The missing quote had once used 'glutton' as a label. {s.id} suggested a kinder revision: 'Describe the choice, then show how the choice can change.' Everyone agreed.",
        f"{c.id} pointed to the word 'glutton' on an outdated card. 'I do get carried away by snacks,' the squirrel said, 'but I am more than one habit.' The team replaced the label with a fair description of the action.",
        f"While rehanging the quote, {h.id} removed the label 'glutton.' 'Names can stick harder than glue,' she said. 'Let's talk about the overeating, not use it as someone's identity.'",
    ]
    world.say(label_lines[params.ending_style % len(label_lines)])
    world.say(f"Beneath the revised quote, they wrote their lesson: {case.lesson}")

    world.para()
    endings = [
        case.ending,
        f"The workshop bell rang, and everyone looked back once at their finished work. {case.ending}",
        f"Nothing in the room was quite where the mystery had begun; the tools were safer, the card was found, and the team knew why. {case.ending}",
        f"{c.id} saved the rest of {case.snack} for later and joined the others at the board. {case.ending}",
    ]
    world.say(endings[params.ending_style % len(endings)])

    world.facts.update(
        hero=h,
        sidekick=s,
        culprit=c,
        quote=q,
        teacup=t,
        table=table,
        board=board,
        resolved=True,
        culprit_hunger=c.memes["hunger"],
        teamwork=h.memes["teamwork"],
        project=case.project,
        trouble=case.trouble,
        clue=case.first_clue,
        discovery=case.discovery,
        cause=case.cause,
        repair=case.repair,
        proof=case.proof,
        lesson=case.lesson,
        ending=case.ending,
        snack=case.snack,
        qa_style=params.telling_mode,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    h, s, c, q = world.facts["hero"], world.facts["sidekick"], world.facts["culprit"], world.facts["quote"]
    style = world.facts["qa_style"] % 4
    mystery_questions = [
        f"What went wrong while the team made {world.facts['project']}?",
        f"Why did work on {world.facts['project']} suddenly stop?",
        f"What mystery interrupted {h.id}'s workshop project?",
        f"Which missing object put the {world.facts['project']} on hold?",
    ]
    clue_questions = [
        f"Which evidence helped {h.id} find the quote card?",
        f"What clue did {h.id} trust instead of the false lead?",
        f"How did the physical evidence guide {h.id} and {s.id} to the card?",
        f"Which detail connected the empty board to the quote card's hiding place?",
    ]
    cause_questions = [
        f"How did {c.id}'s action lead to the missing card?",
        f"What honest explanation did {c.id} give after the card was found?",
        f"Why did the quote card end up away from the board?",
        f"What chain of events did {c.id} admit causing by accident?",
    ]
    repair_questions = [
        "How did teamwork improve the workshop after the mystery was solved?",
        f"What did {h.id}, {s.id}, and {c.id} repair together?",
        "How did the helpers prove that their solution worked?",
        f"What practical change did the team make after finding the {q.label}?",
    ]
    label_questions = [
        "What did the team learn about using the word 'glutton' for someone?",
        "Why did the helpers replace the old label 'glutton'?",
        "How did the revised quote describe a mistake more fairly?",
        "What was kinder than turning overeating into a name for someone?",
    ]
    return [
        QAItem(
            question=mystery_questions[style],
            answer=f"The {q.label} went missing when {world.facts['trouble']}. That interruption stopped the team's project.",
        ),
        QAItem(
            question=clue_questions[style],
            answer=f"{h.id} focused on {world.facts['clue']}. Following that evidence, {h.id} and {s.id} {world.facts['discovery']}.",
        ),
        QAItem(
            question=cause_questions[style],
            answer=f"{c.id} explained that the squirrel {world.facts['cause']}. The team treated it as an accident that still needed an honest repair.",
        ),
        QAItem(
            question=repair_questions[style],
            answer=f"The three helpers {world.facts['repair']}. They checked the result and saw that {world.facts['proof']}.",
        ),
        QAItem(
            question=label_questions[style],
            answer=f"They learned that 'glutton' can be a hurtful label when aimed at a person. Their better lesson was: {world.facts['lesson']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quote?",
            answer="A quote is a line that someone said or wrote down, often because it sounds wise, funny, or important.",
        ),
        QAItem(
            question="What does glutton mean?",
            answer="Glutton is an old word for someone described as eating far more than they need. It can sound insulting when used as a label for a person, so it is kinder to describe the specific behavior instead.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and share the work so a job gets done better and faster.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking a character does inside their own mind while they think things through.",
        ),
        QAItem(
            question="What is a craft workshop?",
            answer="A craft workshop is a place where people make art, build little projects, and use things like paper, glue, and paint.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly mystery set in a {THEME} where a quote card goes missing while a team makes {world.facts['project']}.",
        f"Tell a short story in which an inner monologue helps the hero follow this clue: {world.facts['clue']} End with teamwork and a concrete image.",
        "Create a gentle workshop detective story using the words 'quote' and 'glutton', while making clear that an insulting label should not define a person.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.sidekick, world.culprit, world.quote_card, world.teacup, world.craft_table, world.note_board]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the setting is the craft workshop and the plot includes
% both the quote card and the glutton.
setting(craft_workshop).
requires(craft_workshop, quote).
requires(craft_workshop, glutton).

valid_story(S) :- setting(S), requires(S, quote), requires(S, glutton).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    return "\n".join(
        [
            asp.fact("setting", "craft_workshop"),
            asp.fact("requires", "craft_workshop", "quote"),
            asp.fact("requires", "craft_workshop", "glutton"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import
    models = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(atom.name == "valid_story" for atom in models)
    if ok:
        print("OK: ASP rules recognize the craft workshop story domain.")
        return 0
    print("MISMATCH: ASP rules failed to recognize the story domain.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world set in a craft workshop.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--sidekick", default=None)
    ap.add_argument("--culprit", default=None)
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


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int, base_seed: int) -> StoryParams:
    name = args.name or rng.choice(["Mina", "Tess", "Ivy", "June", "Pia"])
    sidekick = args.sidekick or rng.choice(["Toby", "Luca", "Ned", "Owen", "Ben"])
    culprit = args.culprit or rng.choice(["Chipper", "Nib", "Pip", "Morsel"])
    if name == sidekick:
        raise StoryError("The hero and sidekick must be different characters.")
    if culprit in {name, sidekick}:
        raise StoryError("The culprit must be different from the hero and sidekick.")
    offset = sample_seed - base_seed
    return StoryParams(
        name=name,
        sidekick=sidekick,
        culprit=culprit,
        case=offset % len(CASES),
        telling_mode=(offset // len(CASES)) % 8,
        thought_style=(offset // (len(CASES) * 8)) % 4,
        ending_style=(offset // (len(CASES) * 8 * 4)) % 4,
        seed=sample_seed,
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


CURATED = [
    StoryParams(name="Mina", sidekick="Toby", culprit="Chipper"),
    StoryParams(name="Ivy", sidekick="Luca", culprit="Nib"),
    StoryParams(name="June", sidekick="Owen", culprit="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(a) for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            sample_seed = base_seed + i
            params = resolve_params(args, random.Random(sample_seed), sample_seed, base_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
