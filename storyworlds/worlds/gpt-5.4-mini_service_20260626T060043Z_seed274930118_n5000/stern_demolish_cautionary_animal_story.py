#!/usr/bin/env python3
"""
Storyworld: stern_demolish_cautionary_animal_story

A small animal-story world about a stern warning, a risky demolition, and a
cautious better choice.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Creature:
    id: str
    species: str
    name: str
    role: str
    home: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"risk": 0.0, "damage": 0.0, "caution": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "relief": 0.0, "pride": 0.0})

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Thing:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {"risk": 0.0, "damage": 0.0, "caution": 0.0})


@dataclass
class StoryParams:
    species: str
    hero_name: str
    elder_name: str
    home: str
    risky_thing: str
    safer_fix: str
    incident: str = "survey ribbons"
    telling_mode: str = "morning"
    caution_tool: str = "a bright boundary rope"
    seed: Optional[int] = None


SPECIES = {
    "beaver": {
        "homes": ["riverbank lodge", "pond home"],
        "risky_thing": "old dam",
        "safer_fix": "fresh reeds",
        "actions": ("demolish", "build"),
    },
    "rabbit": {
        "homes": ["burrow tunnel", "meadow den"],
        "risky_thing": "thorny fence",
        "safer_fix": "soft grass path",
        "actions": ("demolish", "tidy"),
    },
    "fox": {
        "homes": ["hill den", "wood edge hollow"],
        "risky_thing": "rickety fence",
        "safer_fix": "quiet path",
        "actions": ("demolish", "repair"),
    },
}

HERO_NAMES = {
    "beaver": ["Milo", "Nina", "Pip", "Tara"],
    "rabbit": ["Mimi", "Luna", "Ollie", "Benny"],
    "fox": ["Ruby", "Fenn", "Sage", "Kiko"],
}

ELDER_NAMES = {
    "beaver": ["Bramble", "Hazel", "Wren"],
    "rabbit": ["Moss", "Fern", "Daisy"],
    "fox": ["Bracken", "Iris", "Rowan"],
}


INCIDENTS = {
    "survey ribbons": {
        "target": "leaning trail shelter",
        "premise": "bright survey ribbons appeared around a leaning shelter before breakfast",
        "impulse": "pull down one loose board to see what the ribbons meant",
        "warning": "Those ribbons mark an adult work zone. Looking is allowed from here; touching is not",
        "clue": "a tiny chalk arrow pointed toward a hidden nest beneath the lowest board",
        "mistake": "The loose board looked unimportant, but it was shielding the nest from falling grit",
        "safe_action": "marked the nest on the foreman's plan and waited behind the boundary while trained builders removed boards from the far side",
        "result": "the nest was moved into a padded wildlife box before the shelter came down in sections",
        "lesson": "a warning boundary can protect lives too small to see at first",
        "ending": "Three hatchlings slept under a clean green cloth while the last board landed softly in the builders' cart",
    },
    "echoing wall": {
        "target": "cracked garden wall",
        "premise": "a hollow garden wall answered every tap with a different echo",
        "impulse": "knock out a cracked brick and peek through the hole",
        "warning": "A cracked wall may be holding weight. Step back and let the mason test it",
        "clue": "one low thump stopped whenever a loaded branch leaned against the wall",
        "mistake": "The crack was not the main danger; the branch was pressing the wall sideways",
        "safe_action": "called the park mason, kept visitors on a marked path, and used a mirror from the safe side to show where the branch touched",
        "result": "adults supported the branch, dismantled the wall from the top, and saved its painted bricks for a bench",
        "lesson": "the first visible crack is not always the true cause",
        "ending": "By sunset, the rescued painted bricks formed a low bench beneath the now-secure tree",
    },
    "rain channel": {
        "target": "abandoned play hut",
        "premise": "storm water began curling around an abandoned play hut scheduled for demolition",
        "impulse": "kick away the soggy bottom slats so the water could escape",
        "warning": "Wet wood can shift without warning. We solve the water problem from dry ground",
        "clue": "floating petals all turned toward one drain blocked by leaves",
        "mistake": "Breaking the hut would not release the water because the blocked drain caused the flood",
        "safe_action": "showed the petal trail to the maintenance crew and helped place warning cones well away from the hut",
        "result": "adults cleared the drain with long tools, then dismantled the dry hut another day",
        "lesson": "careful evidence can prevent needless demolition",
        "ending": "The final puddle slipped through the grate, carrying one yellow petal into the clear channel",
    },
    "sleeping bats": {
        "target": "unused shed",
        "premise": "soft squeaks came from the roof of an unused shed due to be taken down",
        "impulse": "rattle the door so whatever was inside would fly out",
        "warning": "Wild animals need space, and demolition must wait for a wildlife expert",
        "clue": "small shadows appeared only in the roof vent and vanished when voices grew loud",
        "mistake": "The shed was empty of tools but not empty of resting bats",
        "safe_action": "lowered every voice, moved the boundary farther away, and told the wildlife officer exactly where the shadows appeared",
        "result": "the demolition was postponed until the bats moved to a prepared roost under expert supervision",
        "lesson": "being stern can mean protecting frightened animals from a noisy hurry",
        "ending": "Weeks later, moonlight silvered the new bat box as the empty shed came down behind closed gates",
    },
    "keepsake tiles": {
        "target": "old washhouse wall",
        "premise": "an old washhouse wall held tiles painted by generations of animal families",
        "impulse": "pry out a favorite tile before the demolition crew arrived",
        "warning": "Do not enter or pry at the wall. We can ask the crew to recover it safely",
        "clue": "a faded number beside each tile matched a page in the town archive",
        "mistake": "Taking one tile alone would split a picture that continued across six tiles",
        "safe_action": "copied the matching numbers from outside the fence and gave the archive page to the adult conservator",
        "result": "the crew braced the wall and lifted the six-tile picture as one protected panel",
        "lesson": "asking for skilled help can save more than grabbing a treasure",
        "ending": "The complete blue-and-gold fish picture gleamed in the library window that evening",
    },
    "dusty ceiling": {
        "target": "closed seed store",
        "premise": "dust puffed from the ceiling of a closed seed store whenever a cart rolled past",
        "impulse": "dash inside and rescue the labeled seed jars before the ceiling fell",
        "warning": "No object is worth entering an unsafe building. Tell the crew what needs saving",
        "clue": "a delivery list showed that the jars had already been moved to a locked wagon",
        "mistake": "The jars visible through the window were empty display jars, not the seed collection",
        "safe_action": "read the list with the site supervisor and helped neighbors stand beyond the dust screen",
        "result": "trained adults used remote equipment to lower the ceiling inward while the real seeds stayed safe",
        "lesson": "checking facts is braver than rushing toward danger",
        "ending": "Beyond the dust screen, the labeled seed boxes sat in a neat rainbow inside the wagon",
    },
    "crooked footbridge": {
        "target": "closed footbridge",
        "premise": "a closed footbridge tilted after a night of hard rain",
        "impulse": "cross once and loosen the old rope rail before adults demolished it",
        "warning": "Closed means no crossing, even for one quick task. The bank is our safe lookout",
        "clue": "fresh mud beneath the near post showed that the ground, not the rope, had slipped",
        "mistake": "Removing the rope would not straighten a bridge whose foundation had moved",
        "safe_action": "photographed the mud from the marked lookout and guided walkers to the posted detour",
        "result": "engineers dismantled the bridge from both banks and reused its sound planks in a new span",
        "lesson": "a detour is a useful safety tool, not a challenge to defeat",
        "ending": "The old brass bridge bell hung above the new path, chiming as dry paws crossed below",
    },
    "beehive chimney": {
        "target": "empty cottage",
        "premise": "a golden hum trembled inside the chimney of an empty cottage marked for demolition",
        "impulse": "bang a pan nearby to chase the bees away",
        "warning": "Noise may alarm a hive. We back away and call a beekeeper",
        "clue": "bees carried yellow pollen into one loose vent brick but ignored the open windows",
        "mistake": "The bees were nesting inside the chimney, not merely visiting flowers near it",
        "safe_action": "closed the distant footpath, drew the flight route for the beekeeper, and waited indoors with the other youngsters",
        "result": "the beekeeper moved the colony into a hive box before adults dismantled the chimney by hand",
        "lesson": "caution gives experts the quiet time they need",
        "ending": "At dusk, the hive box hummed beside the orchard while the cottage gate stayed firmly shut",
    },
    "library annex": {
        "target": "condemned library annex",
        "premise": "a condemned library annex still showed paper stars taped inside one window",
        "impulse": "slip under the barrier and collect the stars before the wall came down",
        "warning": "Memories can be remade; unsafe walls cannot be trusted",
        "clue": "the librarian's photograph captured every name written on the backs of the stars",
        "mistake": "The paper stars were damp copies; the original class display was already archived",
        "safe_action": "used the photograph at a table across the street to help make a new set while the adult crew worked",
        "result": "the annex was demolished behind screens, and every former pupil received a newly copied star",
        "lesson": "preserving a memory does not require risking a body",
        "ending": "New stars turned slowly above the reading room while rain tapped the safely locked annex gate",
    },
    "fallen lookout": {
        "target": "fallen wooden lookout",
        "premise": "an old wooden lookout had folded onto itself after a windstorm",
        "impulse": "climb the bottom rung and tug free its little weather flag",
        "warning": "A fallen structure can move again. Admire the flag from behind the cones",
        "clue": "the flag string ran beneath a beam that rocked whenever the wind gusted",
        "mistake": "The lowest rung was attached to the same unstable beam as the flag",
        "safe_action": "described the string's path to the rescue crew and checked that the trail remained closed",
        "result": "adults secured each beam, cut the string with a long-handled tool, and dismantled the lookout piece by piece",
        "lesson": "letting go of a prize can be the most courageous choice",
        "ending": "The washed red flag fluttered from the new ground-level trail sign beside a stack of sorted timber",
    },
    "buried pipe": {
        "target": "old greenhouse",
        "premise": "workers found an unknown clay pipe beneath a greenhouse scheduled for demolition",
        "impulse": "scratch away the soil to learn where the pipe went",
        "warning": "Buried pipes may carry water or wires. Only the utility team digs here",
        "clue": "a row of damp mint plants traced a curve toward the pond",
        "mistake": "The pipe was not rubbish; it still carried overflow water away from the greenhouse",
        "safe_action": "mapped the mint from the public path and handed the drawing to the utility engineer",
        "result": "adults capped and rerouted the pipe before taking down the greenhouse frame",
        "lesson": "what looks abandoned may still have an important job",
        "ending": "Clean water burbled through the new channel as mint leaves nodded along its edge",
    },
    "festival arch": {
        "target": "cracked festival arch",
        "premise": "a cracked festival arch leaned over the empty square after the celebration",
        "impulse": "shake loose the last ribbon before the demolition lift arrived",
        "warning": "We do not stand beneath a leaning arch. Point out the ribbon from the safe line",
        "clue": "the ribbon was tied around a wooden peg that also pinned two cracked panels together",
        "mistake": "A harmless-looking ribbon had become part of the arch's temporary support",
        "safe_action": "told the lifting crew about the peg and helped clear the square using the posted side streets",
        "result": "adults strapped the panels together, lowered the arch flat, and untied the ribbon afterward",
        "lesson": "small details can matter when a structure is unstable",
        "ending": "The saved ribbon curled around the town noticeboard while the square stood open and quiet",
    },
}

TELLING_MODES = (
    "morning", "question", "warning-first", "discovery", "dialogue-first",
    "weather", "memory", "countdown", "quiet", "community",
)

CAUTION_TOOLS = (
    "a bright boundary rope", "three painted cones", "a chalk safety line",
    "a folding warning sign", "a ribboned detour marker", "a viewing flag",
)

REASONING_BEATS = (
    "{hero} compared the tempting shortcut with the marked safe route and saw that only one of them left room for adults to work.",
    '"What could move if I touch it?" {hero} asked. {elder} answered by pointing out the parts that carried weight.',
    "For one patient minute, {hero} watched the site instead of acting. That minute revealed details a hurried paw would have missed.",
    "{hero} sketched the danger from outside the boundary, then turned the page around so {elder} could check the drawing.",
    '"My idea was quick, but it was not a plan," {hero} said. A real plan needed distance, skilled adults, and a way to protect bystanders.',
    "{elder} asked {hero} to name the hazard, the safe boundary, and the person responsible for the work. The three answers slowed the impulse to rush.",
    "The youngster listened for a full ten breaths. Nothing became less interesting, but the danger became much easier to understand.",
    "{hero} imagined the shortcut going wrong, then imagined everyone staying behind the marker while an expert acted. The second picture made the choice clear.",
    "Together they made two lists: what they knew and what they only guessed. The risky idea belonged entirely in the guessing list.",
    "{hero} repeated the warning in new words: look from here, report the clue, and leave every heavy part to the crew.",
    "A neighbor offered another quick solution, but {hero} now asked for evidence before agreeing. {elder}'s stern pause had already changed the conversation.",
    "Instead of treating caution as fear, {hero} treated it as a job: notice carefully, tell clearly, and wait where it was safe.",
)

CLOSING_EXCHANGES = (
    '"You listened before you acted," {elder} said. "That is how a helper earns trust."',
    "{hero} thanked {elder} for making the warning plain, and {elder} thanked the youngster for reporting the clue.",
    '"Next time I will begin at the boundary," {hero} promised, "with my eyes open and my paws still."',
    "The pair added the newly discovered hazard to the crew's noticeboard so the next visitor would understand the closed area too.",
    "Before leaving, {hero} showed a younger neighbor where to stop and whom to call, passing the caution forward.",
    '"Stern did not mean angry," {hero} reflected. "It meant the danger was too important to mumble about."',
    "{elder} invited {hero} to watch the crew's final safety check from the public path, where questions were welcome and paws were protected.",
    "They counted every creature outside the boundary before the work ended, then celebrated the careful result together.",
)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.creatures: dict[str, Creature] = {}
        self.things: dict[str, Thing] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        chunk: list[str] = []
        for line in self.lines:
            if line == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            out.append(" ".join(chunk))
        return "\n\n".join(out)


def build_world(params: StoryParams) -> World:
    world = World(params)
    incident = INCIDENTS[params.incident]
    hero = Creature("hero", params.species, params.hero_name, "young", params.home, ["curious", "learning caution"])
    elder = Creature("elder", params.species, params.elder_name, "stern elder", params.home, ["stern", "protective"])
    thing = Thing("thing", params.risky_thing, "demolition site")
    fix = Thing("fix", params.safer_fix, "restoration material")
    boundary = Thing("boundary", params.caution_tool, "safety marker")

    world.creatures[hero.id] = hero
    world.creatures[elder.id] = elder
    world.things[thing.id] = thing
    world.things[fix.id] = fix
    world.things[boundary.id] = boundary

    openings = {
        "morning": f"On a clear morning at {params.home}, {hero.name}, a young {params.species}, found that {incident['premise']}.",
        "question": f'"Why is that closed?" {hero.name} asked when {incident["premise"]} at {params.home}.',
        "warning-first": f'"Stop at {params.caution_tool}," called {elder.name}. At {params.home}, {incident["premise"]}.',
        "discovery": f"The first unusual thing {hero.name} discovered at {params.home} was this: {incident['premise']}.",
        "dialogue-first": f'"I can fix this quickly," said {hero.name}, after {incident["premise"]} at {params.home}.',
        "weather": f"After the weather changed at {params.home}, {incident['premise']}; {hero.name} hurried over to investigate.",
        "memory": f"{hero.name} had once helped mend things at {params.home}, so when {incident['premise']}, the young {params.species} expected another simple repair.",
        "countdown": f"The adult demolition crew would arrive after lunch. Before then, {incident['premise']} at {params.home}, and {hero.name} noticed it.",
        "quiet": f"A strange hush settled over {params.home} when {incident['premise']}. {hero.name} crept closer to look.",
        "community": f"Everyone near {params.home} was discussing how {incident['premise']}. Curious {hero.name} went to find {elder.name}.",
    }
    world.say(openings[params.telling_mode])
    world.say(f"The {params.risky_thing} was scheduled for careful demolition by trained adults, with {params.caution_tool} keeping young animals at a safe distance.")
    world.say(f"Still, {hero.name}'s first impulse was to {incident['impulse']}.")
    world.para()

    hero.meters["risk"] += 1
    thing.meters["risk"] += 1
    world.say(f'{elder.name} planted both feet and gave a stern warning: "{incident["warning"]}."')
    world.say(f"{incident['mistake']}. That meant {hero.name}'s idea could endanger someone or make the adult demolition harder.")
    beat_rng = random.Random((params.seed or 0) ^ 0x5EEDCAFE)
    world.say(beat_rng.choice(REASONING_BEATS).format(hero=hero.name, elder=elder.name))
    hero.memes["worry"] += 1
    elder.memes["worry"] += 1
    world.para()

    turn_leads = {
        "morning": "In the slanting morning light,",
        "question": "After asking one more careful question,",
        "warning-first": "Because the warning named the danger clearly,",
        "discovery": "Looking from the safe side instead,",
        "dialogue-first": '"I will help without crossing," the youngster decided, and',
        "weather": "When the air grew still enough to observe,",
        "memory": "Remembering that good repairs begin with evidence,",
        "countdown": "Without racing the crew's clock,",
        "quiet": "In the quiet, without touching anything,",
        "community": "With the neighbors watching from the marked path,",
    }
    world.say(f"{turn_leads[params.telling_mode]} {hero.name} spotted the useful clue: {incident['clue']}.")
    world.say(f'"I thought demolish meant knocking fast," {hero.name} admitted. "Now I think it means planning how to take something down safely."')
    world.say(f"From behind {params.caution_tool}, {hero.name} {incident['safe_action']}.")
    hero.meters["caution"] += 1
    elder.meters["caution"] += 1
    boundary.meters["caution"] += 1
    world.para()

    thing.meters["damage"] = 0.0
    fix.meters["caution"] += 1
    hero.memes["relief"] += 1
    elder.memes["pride"] += 1
    world.say(f"The plan worked: {incident['result']}.")
    world.say(f"Later, {hero.name} and {elder.name} used {params.safer_fix} where it could help restore the cleared place, never as a reason to enter the work zone.")
    world.say(f"{hero.name} learned that {incident['lesson']}. Caution meant studying the danger and leaving demolition to trained adults; a stern voice could carry kindness when it made that danger unmistakable.")
    closing_rng = random.Random((params.seed or 0) ^ 0xC1051A6)
    world.say(closing_rng.choice(CLOSING_EXCHANGES).format(hero=hero.name, elder=elder.name))
    world.say(f"{incident['ending']}.")

    world.facts.update(
        hero=hero,
        elder=elder,
        thing=thing,
        fix=fix,
        boundary=boundary,
        action=SPECIES[params.species]["actions"][0],
        premise=incident["premise"],
        impulse=incident["impulse"],
        clue=incident["clue"],
        mistaken_belief=incident["mistake"],
        safer_action=incident["safe_action"],
        result=incident["result"],
        lesson=incident["lesson"],
        ending=incident["ending"],
        home=params.home,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Creature = f["hero"]
    elder: Creature = f["elder"]
    thing: Thing = f["thing"]
    return [
        f'Write a short animal story for young children about {hero.name}, {elder.name}, and a stern warning after {f["premise"]}.',
        f"Tell a cautionary story where a little {hero.species} wants to demolish {thing.label}, notices that {f['clue']}, and helps safely from outside the work zone.",
        f"Write an animal story in which trained adults control demolition and {hero.name} learns that {f['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Creature = f["hero"]
    elder: Creature = f["elder"]
    thing: Thing = f["thing"]
    return [
        QAItem(
            question=f"What did {hero.name} first want to do near the {thing.label}?",
            answer=f"{hero.name} first wanted to {f['impulse']}. That was unsafe inside an adult demolition zone, and {hero.name} later understood that {f['mistaken_belief'].lower()}.",
        ),
        QAItem(
            question=f"What clue changed {hero.name}'s understanding?",
            answer=f"{hero.name} noticed that {f['clue']}. The clue showed that rushing to demolish something could miss the real problem.",
        ),
        QAItem(
            question=f"How did {hero.name} help without entering the demolition zone?",
            answer=f"From behind {f['boundary'].label}, {hero.name} {f['safer_action']}. Trained adults remained responsible for the demolition itself.",
        ),
        QAItem(
            question=f"What happened because {hero.name} listened to {elder.name}'s stern warning?",
            answer=f"Because {hero.name} listened to {elder.name}, the safer plan succeeded: {f['result']}. {hero.name} learned that {f['lesson']}.",
        ),
        QAItem(
            question="What final image shows that the danger passed?",
            answer=f"The closing image is this: {f['ending']}. It makes the safe result visible instead of merely claiming that everything was fine.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does stern mean?",
            answer="Stern means serious and firm, like a grown-up who is warning you clearly because safety matters.",
        ),
        QAItem(
            question="What does demolish mean?",
            answer="Demolish means to tear something down or break it apart, usually carefully and with a plan.",
        ),
        QAItem(
            question="What is caution?",
            answer="Caution is careful behavior that helps keep people safe and avoids unnecessary trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for c in world.creatures.values():
        lines.append(f"{c.id}: species={c.species} meters={dict(c.meters)} memes={dict(c.memes)}")
    for t in world.things.values():
        lines.append(f"{t.id}: label={t.label} kind={t.kind} meters={dict(t.meters)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is cautionary when a risky demolition is prevented by caution.
cautionary_story(S) :- stern_warning(S), risky_demolish(S), choose_caution(S).

stern_warning(S) :- story(S), elder_stern(S).
risky_demolish(S) :- story(S), wants_demolish(S), unsafe(S).
choose_caution(S) :- story(S), safer_choice(S).
"""


def asp_facts(params: StoryParams) -> str:
    import asp
    lines = [
        asp.fact("story", "s1"),
        asp.fact("elder_stern", "s1"),
        asp.fact("wants_demolish", "s1"),
        asp.fact("unsafe", "s1"),
        asp.fact("safer_choice", "s1"),
    ]
    return "\n".join(lines)


def asp_program() -> str:
    params = StoryParams(
        species="beaver",
        hero_name="Milo",
        elder_name="Bramble",
        home="riverbank lodge",
        risky_thing="old dam",
        safer_fix="fresh reeds",
    )
    return f"{asp_facts(params)}\n{ASP_RULES}\n#show cautionary_story/1.\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "cautionary_story"))
    if atoms == {("s1",)}:
        print("OK: ASP gate matches the cautionary pattern.")
        return 0
    print("MISMATCH: ASP did not recognize the cautionary story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about stern caution and risky demolition.")
    ap.add_argument("--species", choices=sorted(SPECIES))
    ap.add_argument("--hero-name")
    ap.add_argument("--elder-name")
    ap.add_argument("--home")
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
    species = args.species or rng.choice(sorted(SPECIES))
    cfg = SPECIES[species]
    home = args.home or rng.choice(cfg["homes"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES[species])
    elder_name = args.elder_name or rng.choice(ELDER_NAMES[species])
    incident = rng.choice(sorted(INCIDENTS))
    return StoryParams(
        species=species,
        hero_name=hero_name,
        elder_name=elder_name,
        home=home,
        risky_thing=INCIDENTS[incident]["target"],
        safer_fix=cfg["safer_fix"],
        incident=incident,
        telling_mode=rng.choice(TELLING_MODES),
        caution_tool=rng.choice(CAUTION_TOOLS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(
        species="beaver", hero_name="Milo", elder_name="Bramble",
        home="riverbank lodge", risky_thing="abandoned play hut", safer_fix="fresh reeds",
        incident="rain channel", telling_mode="weather", caution_tool="three painted cones",
    ),
    StoryParams(
        species="rabbit", hero_name="Mimi", elder_name="Moss",
        home="meadow den", risky_thing="unused shed", safer_fix="soft grass path",
        incident="sleeping bats", telling_mode="quiet", caution_tool="a bright boundary rope",
    ),
    StoryParams(
        species="fox", hero_name="Ruby", elder_name="Bracken",
        home="hill den", risky_thing="cracked festival arch", safer_fix="quiet path",
        incident="festival arch", telling_mode="warning-first", caution_tool="a chalk safety line",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
