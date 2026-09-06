#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tar_endanger_thin_flower_field_repetition_animal.py
=============================================================================================================================

A child-safe animal-story world set in a flower field, built around repetition,
tar, observation, and protecting thin flowers.

Premise:
- A small animal loves the flower field.
- Sticky tar threatens the thin stems and the little creatures who hop there.
- The helper repeats warnings and checks while a trained adult handles the tar.

Story shape:
- Beginning: animals play in a flower field.
- Middle: one of several tar incidents endangers thin flowers or visiting animals.
- Turn: a clue changes the hero's first plan; warnings and checks are repeated.
- Ending: trained help removes the hazard, and a concrete image proves the change.

The world is deliberately small and constraint-checked:
- tar is a real hazard in the flower field
- thin stems are at risk
- repetition is used for safe warnings, counts, routes, and checks
- the resolution must actually protect the endangered flowers
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "mouse", "bird", "squirrel"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the flower field"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    fragile: bool = True


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    repeated_action: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "flower_field": Setting(place="the flower field", affords={"tar_walk"}),
}

ACTIVITIES = {
    "tar_walk": Activity(
        id="tar_walk",
        verb="cross the flower field",
        gerund="crossing the flower field",
        rush="dash toward the flowers",
        hazard="tar",
        soil="stuck with tar",
        keyword="tar",
        tags={"tar", "field", "thin", "repetition"},
    )
}

PRIZES = {
    "flowers": Prize(
        label="flowers",
        phrase="a patch of thin flowers",
        type="flowers",
        fragile=True,
    )
}

TOOLS = {
    "washing_rinse": Tool(
        id="washing_rinse",
        label="a little pail of water",
        prep="fetch a little pail of water",
        tail="kept rinsing the sticky spots away",
        repeated_action="again and again",
    ),
    "leaf_pat": Tool(
        id="leaf_pat",
        label="soft leaves",
        prep="gather soft leaves",
        tail="kept patting the tar so it would lift off",
        repeated_action="over and over",
    ),
}

ANIMALS = [
    ("Pip", "rabbit"),
    ("Nia", "mouse"),
    ("Toto", "squirrel"),
    ("Momo", "bird"),
    ("Lulu", "fox"),
]

TRAITS = ["small", "curious", "gentle", "brave", "cheerful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    animal: str
    trait: str
    scenario: str = ""
    telling: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    id: str
    opening: str
    discovery: str
    danger: str
    first_idea: str
    clue: str
    warning: str
    expert: str
    safe_work: str
    repeated_check: str
    proof: str
    ending: str
    lesson: str


INCIDENTS = {
    item.id: item
    for item in [
        Incident(
            "tipped_pail",
            "A gardener's path-repair cart bumped over a root, and a sealed pail rolled loose.",
            "A dark ribbon of tar had escaped beneath its lid beside the nodding poppies.",
            "One more roll could carry the pail into a bed of thin poppy stems.",
            "The little animal started to nose the heavy pail uphill.",
            "A black shine on one paw showed that touching the spill would only spread it.",
            '"Back from the shiny patch! Back, back!" the animal called.',
            "Gardener Sol returned with gloves, a barrier board, and absorbent sand.",
            "Sol righted the pail, covered the spill with sand, and lifted the soiled earth into a safe container.",
            "The animal paced the border again and again, checking that no paw or stem crossed it.",
            "Every poppy lifted cleanly when the breeze returned.",
            "Three red petals rested on the dry barrier board like tiny flags.",
            "A quick warning can be braver than a quick rescue.",
        ),
        Incident(
            "tracked_boots",
            "After a footpath was repaired, muddy bootprints crossed the flower field.",
            "The last prints were glossy with tar and pointed toward a nursery of thin lupines.",
            "Bees were following the same short route between the low blossoms.",
            "The animal thought of rubbing each print with a bunch of grass.",
            "A grass tip stuck fast in the first print, proving that rubbing would widen the marks.",
            '"Use the clean path, please! This way, this way!" the animal repeated.',
            "Ranger Mira arrived with marker cones, gloves, and clean absorbent pads.",
            "Mira blocked the shortcut and removed each sticky clump without trampling the flowers.",
            "The animal counted the prints forward, then backward, again and again until all were gone.",
            "The bees visited every lupine without touching a dark mark.",
            "At sunset, their wings flickered above twelve unbent purple spires.",
            "Evidence should guide the repair, not the first hurried idea.",
        ),
        Incident(
            "rain_channel",
            "A night shower filled the field's shallow channels with silver water.",
            "At dawn, one channel carried beads of tar from a damaged path edge.",
            "The water was steering the sticky beads toward thin bluebells downhill.",
            "The animal began scratching a new ditch with both front paws.",
            "A floating petal spun toward the bluebells and revealed the water's exact route.",
            '"Close the lower trail! Wait here, wait here!" the animal told the others.',
            "Groundskeeper Imani brought gloves, absorbent socks, and a small clean-earth berm.",
            "Imani stopped the flow above the flowers, collected the tar, and replaced the stained soil.",
            "The animal watched three leaf boats at a time, repeating the test until each turned away from the blooms.",
            "Fresh water now curved around the bluebells instead of through them.",
            "One clear drop hung under the thinnest bell and reflected the morning sky.",
            "Careful tests can reveal where a hidden danger is traveling.",
        ),
        Incident(
            "butterfly_patch",
            "A warm afternoon brought painted-lady butterflies down to the field.",
            "The animal noticed one butterfly veer sharply above a tar-speckled landing patch.",
            "The sticky specks could trap delicate feet beside the thin milkweed stalks.",
            "The animal wanted to cover the patch with loose petals.",
            "A tossed petal landed flat and would not lift, showing why a cover would hide the danger.",
            '"Land by the stones! Stones, stones!" the animal called to the fluttering visitors.',
            "Wildlife gardener Bea came with gloves, a screen, and a tray for contaminated soil.",
            "Bea screened the patch, removed every speck, and set a clean damp landing stone nearby.",
            "The animal circled slowly again and again, watching each butterfly choose a safe perch.",
            "The painted ladies opened and closed their wings on the clean stone.",
            "Orange wings rose around the milkweed while its thin leaves stayed free.",
            "A danger should be made visible before it can be made safe.",
        ),
        Incident(
            "sticky_paw",
            "During a game of follow-the-scent, a young hedgehog strayed beside the path works.",
            "Its front paw touched a small drop of tar before the watching animal called a halt.",
            "Walking farther could endanger both the hedgehog and the thin flowers ahead.",
            "The animal almost tugged the paw free with its teeth.",
            "A second dark dot on the soil showed that every frightened step spread the tar.",
            '"Stay still; help is coming. Still, still," the animal soothed.',
            "Wildlife carer Noor arrived with a towel-lined carrier and animal-safe cleaning supplies.",
            "Noor lifted the hedgehog, treated its paw away from the field, and had the spill professionally contained.",
            "The animal checked each footprint again and again while Noor marked the affected soil.",
            "The hedgehog returned later with a clean paw and an easy step.",
            "Its tiny tracks ended beside a white clover, with no black dots between them.",
            "When an animal touches a hazard, keep it still and call a trained adult.",
        ),
        Incident(
            "windblown_sign",
            "A gust toppled a KEEP OFF sign beside a freshly sealed path.",
            "The sign's tar-dark base slid toward a stand of thin foxgloves.",
            "Another gust could push the sticky base through the hollow stems.",
            "The animal leaned against the sign to shove it back alone.",
            "The scraping sound grew louder, warning that the rough edge was cutting the soil.",
            '"Stop at the rope! Stop at the rope!" the animal cried to the running field mice.',
            "Park keeper Ren brought gloves, wedges, and a clean board.",
            "Ren pinned the sign safely, slid the board beneath it, and removed the contaminated strip of soil.",
            "The animal repeated a wind check after every gust until the sign stayed firm.",
            "The foxgloves rang softly without one stem bending.",
            "A ladybird climbed the upright sign while the last gust passed harmlessly by.",
            "Stopping others first can prevent one problem from becoming many.",
        ),
        Incident(
            "wagon_drip",
            "A supply wagon carried sealed tar past the flower field to repair a distant lane.",
            "A loose cap left spaced drops behind one wheel near thin daisies.",
            "The next wagon pass would press those drops deeper and scatter them wider.",
            "The animal considered rolling the wagon away before anyone noticed.",
            "The drops formed a repeating trail, and the smallest gaps pointed straight back to the loose cap.",
            '"Wheel still! Cap loose! Wheel still!" the animal shouted.',
            "Driver Ana stopped, put on gloves, and called the maintenance team.",
            "The team sealed the cap, fenced the dotted trail, and removed each contaminated scoop of earth.",
            "The animal followed the spaces again and again, placing a twig marker beside every missed drop.",
            "A final walk found clean soil between the wagon and the daisies.",
            "In the dusk, white daisy faces made an unbroken line beside the quiet wheel.",
            "A repeated pattern can lead a careful observer back to its cause.",
        ),
        Incident(
            "nest_fiber",
            "A blackbird gathered dry grass for a nest above the flower field.",
            "The animal saw a glossy tar thread clinging to one strand near thin irises.",
            "The bird might weave the sticky strand into its nest or brush it across the blooms.",
            "The animal jumped to snatch the strand from the bird's beak.",
            "The bird dropped it when the strand caught on a stone, revealing several more below.",
            '"Clean grass here! Here, here!" the animal called from a safe pile.',
            "Habitat worker Jo arrived with gloves, a covered bin, and clean nesting grass.",
            "Jo removed the tainted fibers, traced them to a cracked sealant sack, and closed the area.",
            "The animal watched each new beakful again and again until only clean grass went upward.",
            "The blackbird finished a dry, springy nest without a sticky strand.",
            "A pale feather settled inside the nest as the irises swayed below.",
            "Helping wildlife means offering a safe choice and letting a trained adult handle hazards.",
        ),
        Incident(
            "mower_splash",
            "The field mower stopped beside a path that had been patched that morning.",
            "A wheel had flicked tiny tar spots toward a row of thin cosmos stems.",
            "Restarting the mower could spray more spots across the flowers.",
            "The animal hurried toward the switch, meaning to fix everything alone.",
            "A fan-shaped spray on one stone showed that the wheel, not the engine, was spreading the tar.",
            '"Do not start it! Not yet, not yet!" the animal repeated.',
            "Caretaker Luis disconnected the mower and brought the grounds crew with protective gloves.",
            "They cleaned the equipment in the service yard and carefully removed the spotted soil.",
            "The animal inspected one stone, one leaf, and one stem again and again down the whole row.",
            "No new spots appeared when a clean mower later took another route.",
            "Pink cosmos petals trembled above a spotless border in the evening light.",
            "Finding the direction of a pattern can identify what caused it.",
        ),
        Incident(
            "fallen_board",
            "Workers had laid a clean board across a muddy corner to protect the flowers.",
            "Overnight, the board flipped onto its tar-sealed underside beside thin buttercups.",
            "Any animal crossing it could carry tar from the underside into the field.",
            "The animal tried to flip the board with a long branch.",
            "The branch stuck at once, proving the hidden side was still tacky.",
            '"Around the corner! Around, around!" the animal directed the morning walkers.',
            "Trail steward Mei arrived with gloves, supports, and a lidded transport sheet.",
            "Mei isolated the board, wrapped it without scraping the ground, and checked the soil beneath.",
            "The animal repeated the detour directions until every visitor used the clean curve.",
            "The buttercups remained upright, and the branch was collected with the board.",
            "Yellow cups shone beside a new clean stepping stone after sunrise.",
            "A hidden surface can still be dangerous, so test from a safe distance and seek help.",
        ),
        Incident(
            "warm_seep",
            "At noon, sunlight warmed an old path seam along the flower field.",
            "A soft bead of tar squeezed from the seam near thin snapdragons.",
            "The heat could make the bead creep farther before the cool evening.",
            "The animal thought shade leaves pressed on top would solve it.",
            "One leaf edge sank into the bead, showing that direct covering would become another sticky trap.",
            '"Use the far gate today! Far gate, far gate!" the animal announced.',
            "Path engineer Sam brought cones, gloves, mineral absorbent, and a heat-safe patch kit.",
            "Sam cooled and contained the seep, removed the affected soil, and repaired the seam correctly.",
            "The animal checked the marker line again and again as the afternoon stayed warm.",
            "The repaired seam remained firm, and no new bead formed.",
            "At twilight, each snapdragon cast a thin clean shadow across the mended path.",
            "A repair must address the source of a hazard, not merely hide its surface.",
        ),
        Incident(
            "lost_tool",
            "A volunteer team finished marking a path and counted its tools before leaving.",
            "One tar-stained spreader was missing beside a patch of thin asters.",
            "A curious animal might step on the dark tool hidden under grass.",
            "The animal began sweeping the grass aside with its tail.",
            "Three pressed blades made a straight line, a clue that the tool had slid rather than flown.",
            '"Feet off the grass! Look, look, but do not touch!" the animal called.',
            "Volunteer leader Dee returned with gloves, flags, and a tool case.",
            "Dee followed the pressed grass, lifted the spreader into its case, and removed two stained clods.",
            "The animal repeated the team's count again and again until every tool and flag matched the list.",
            "The search ended with clean paws, twelve tools, and every aster standing.",
            "A blue aster leaned over the closed tool case, untouched by the tar below.",
            "Counting and recounting can catch a small mistake before it causes harm.",
        ),
    ]
}

TELLINGS = ["clue_first", "dialogue_first", "quiet_build", "question_turn", "action_turn", "field_view", "friend_view", "lesson_echo"]
OPENERS = [
    "Morning light moved slowly over the flower field.",
    "The flower field hummed with bees and small wings.",
    "Beyond the clean path, the flower field was waking.",
    "A breeze combed through the flower field without bending its thinnest stems.",
    "The smallest sounds carried clearly across the flower field that day.",
    "Dew still jeweled the flower field when the trouble began.",
    "The flower field looked peaceful from the old gate.",
    "Petals nodded all across the flower field under a clear sky.",
]
REACTIONS = [
    "Its heart thumped, but it stopped to look before acting.",
    "It took one careful step back and studied what had changed.",
    "For a moment it wanted to hurry; then it remembered that sticky hazards spread.",
    "It listened, sniffed, and kept its paws on clean ground.",
    "It called the nearby animals together without letting them crowd the spot.",
    "It marked the safe side with three pale pebbles.",
    "It breathed slowly and searched for a clue from beyond the dark patch.",
    "It chose a lookout place where it could see both the path and the flowers.",
]
COMMUNITY_LINES = [
    "A rabbit guided beetles around the marker while a wren carried the warning farther.",
    "Two mice guarded the clean trail, repeating the warning in small clear voices.",
    "A squirrel watched the upper path while a robin watched the flowers below.",
    "The field's visitors formed a patient line along the safe stones.",
    "Even the busiest bees shifted to the flowers beyond the boundary.",
    "The animals passed the message from the gate to the farthest clover patch.",
    "A young vole fetched a bright flag but left the sticky place untouched.",
    "From clean ground, three friends helped count every marker.",
]


def tar_is_threat(activity: Activity, prize: Prize) -> bool:
    return activity.hazard == "tar" and prize.fragile


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if tar_is_threat(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: tar, thin flowers, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=[a for _, a in ANIMALS])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--scenario", choices=INCIDENTS)
    ap.add_argument("--telling", choices=TELLINGS)
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


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["tar"] = actor.meters.get("tar", 0.0) + 1.0
    world.facts["tar_seen"] = True
    world.facts["tar_threat"] = True
    if narrate:
        world.say(f"{actor.id} got tar on its paws while {activity.gerund}.")


def _tar_spread(world: World, actor: Entity, prize: Entity) -> None:
    sig = ("tar_spread", actor.id, prize.id)
    if sig in world.fired:
        return
    if actor.meters.get("tar", 0.0) >= THRESHOLD:
        world.fired.add(sig)
        prize.meters["tar"] = prize.meters.get("tar", 0.0) + 1.0
        prize.meters["endangered"] = prize.meters.get("endangered", 0.0) + 1.0


def _repeat_clean(world: World, actor: Entity, prize: Entity, tool: Tool) -> None:
    sig = ("repeat_clean", actor.id, prize.id)
    if sig in world.fired:
        return
    if actor.memes.get("repetition", 0.0) >= 1.0:
        world.fired.add(sig)
        prize.meters["tar"] = max(0.0, prize.meters.get("tar", 0.0) - 1.0)
        if prize.meters["tar"] <= 0.0:
            prize.meters["endangered"] = 0.0
        world.say(f"{actor.id} used {tool.label} {tool.repeated_action}.")


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters.get("tar", 0.0) >= THRESHOLD:
                for prize in world.entities.values():
                    if prize.kind != "thing":
                        continue
                    before = prize.meters.get("tar", 0.0)
                    _tar_spread(world, actor, prize)
                    if prize.meters.get("tar", 0.0) != before:
                        changed = True
                        if narrate:
                            world.say("The sticky tar started to endanger the thin flowers.")
            if actor.memes.get("repetition", 0.0) >= 1.0:
                for prize in world.entities.values():
                    if prize.kind == "thing":
                        before = prize.meters.get("tar", 0.0)
                        _repeat_clean(world, actor, prize, TOOLS["washing_rinse"])
                        if prize.meters.get("tar", 0.0) != before:
                            changed = True


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    name: str,
    animal: str,
    trait: str,
    incident: Incident,
    telling: str,
    rng: random.Random,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=animal))
    hero.memes["repetition"] = 1.0
    prize = world.add(Entity(id="flowers", kind="thing", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    prize.meters.update(tar=1.0, endangered=1.0)

    opener = rng.choice(OPENERS)
    reaction = rng.choice(REACTIONS)
    community = rng.choice(COMMUNITY_LINES)
    introductions = {
        "clue_first": f"{opener} {hero.id}, a {trait} {animal}, noticed that one familiar detail was wrong.",
        "dialogue_first": f'"What changed?" wondered {hero.id}, a {trait} {animal}, as {opener.lower()}',
        "quiet_build": f"{opener} At first, {hero.id}, a {trait} {animal}, heard only petals brushing one another.",
        "question_turn": f"How could a peaceful flower field become unsafe? {hero.id}, a {trait} {animal}, was about to find out.",
        "action_turn": f"{hero.id}, a {trait} {animal}, was making a careful round of the flower field. {opener}",
        "field_view": f"Thin flowers filled the field from the gate to the creek. {opener} A {trait} {animal} named {hero.id} knew every bend.",
        "friend_view": f"The smaller animals trusted {hero.id}, a {trait} {animal}, to notice trouble in their flower field. {opener}",
        "lesson_echo": f"{hero.id}, a {trait} {animal}, liked to say, 'Look twice before you leap.' {opener}",
    }
    world.say(introductions[telling])
    world.say(incident.opening)
    world.para()

    if telling in {"clue_first", "quiet_build"}:
        world.say(incident.discovery)
        world.say(incident.clue)
        world.say(f"Now {hero.id} understood the danger. {incident.danger}")
    elif telling in {"question_turn", "field_view"}:
        world.say(incident.discovery)
        world.say(f"Why did that matter? {incident.danger}")
        world.say(incident.clue)
    else:
        world.say(incident.discovery)
        world.say(incident.danger)
        world.say(incident.clue)
    world.say("If it spread, the tar would endanger the field's thin flowers.")
    world.facts.update(tar_seen=True, tar_threat=True)
    world.para()

    world.say(incident.first_idea)
    world.say(reaction)
    if telling == "dialogue_first":
        world.say(incident.warning)
        world.say(f"That repetition gave everyone time to move onto clean ground. {community}")
    elif telling == "friend_view":
        world.say(community)
        world.say(incident.warning)
    else:
        world.say(incident.warning)
        world.say(community)
    world.say("This was useful repetition: the warning traveled again and again while everyone stayed away from the tar.")
    world.para()

    if telling in {"action_turn", "lesson_echo"}:
        world.say(incident.expert)
        world.say(f"The animal stayed behind the boundary while the trained adult worked. {incident.safe_work}")
        world.say(incident.repeated_check)
    else:
        world.say(f"Help came soon. {incident.expert}")
        world.say(incident.safe_work)
        world.say(incident.repeated_check)
    prize.meters.update(tar=0.0, endangered=0.0)
    world.facts["resolved"] = True
    world.para()

    closing_leads = [
        "At last, the proof was plain.",
        "Only when the final check was complete did the boundary come down.",
        "The field grew quiet enough to test the repair.",
        "No one guessed that the danger was over; they checked.",
        "The repeated checks finally brought good news.",
        "By evening, the careful work had changed the whole scene.",
        "Then came the small sign everyone had waited for.",
        "The animals looked once more from the clean side of the markers.",
    ]
    world.say(f"{rng.choice(closing_leads)} {incident.proof}")
    world.say(incident.ending)
    if telling == "lesson_echo":
        world.say(f"{hero.id} repeated the lesson softly: {incident.lesson}")
    else:
        world.say(f"{hero.id} carried one lesson home: {incident.lesson}")

    world.facts.update(
        hero=hero,
        prize=prize,
        activity=activity,
        setting=setting,
        incident=incident,
        telling=telling,
        expert=incident.expert.split(" arrived", 1)[0].split(" returned", 1)[0],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    incident = f["incident"]
    return [
        f"Write a child-safe animal story in a flower field about {hero.id} noticing {incident.id.replace('_', ' ')}.",
        f"Tell a gentle story where a {hero.type} uses repetition to warn others when tar could endanger thin flowers.",
        "Write an animal story in which observation, adult help, and repeated checks lead to a concrete safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    incident = f["incident"]
    incident_label = incident.id.replace("_", " ")
    qa = [
        QAItem(
            question=f"Who noticed the danger during the {incident_label} incident?",
            answer=f"{hero.id}, a {hero.type} who watched over the flower field, noticed the danger.",
        ),
        QAItem(
            question=f"What specific tar danger did {hero.id} discover during the {incident_label} incident?",
            answer=incident.danger,
        ),
        QAItem(
            question=f"What clue changed {hero.id}'s plan during the {incident_label} incident?",
            answer=incident.clue,
        ),
        QAItem(
            question=f"How did {hero.id} use repetition safely during the {incident_label} incident?",
            answer=f"{incident.warning} Later, {incident.repeated_check[0].lower() + incident.repeated_check[1:]}",
        ),
        QAItem(
            question=f"How did a trained adult handle the tar in the {incident_label} incident?",
            answer=f"A trained adult took charge: {incident.safe_work}",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What final image ended {hero.id}'s {incident_label} story?",
            answer=incident.ending,
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tar?",
            answer="Tar is a sticky, dark substance that can cling to things and make them dirty.",
        ),
        QAItem(
            question="What does thin mean?",
            answer="Thin means something is not wide or thick, so it can bend or break more easily.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same helpful action again and again.",
        ),
        QAItem(
            question="What should a child do after finding tar or another unknown sticky substance?",
            answer="A child should stay on clean ground, warn others away, and tell a trusted adult rather than touching or cleaning it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
threatened(P) :- tar_on(A), thin(P).
resolved(P) :- threatened(P), cleaned(P).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "flower_field")]
    lines.append(asp.fact("affords", "flower_field", "tar_walk"))
    lines.append(asp.fact("activity", "tar_walk"))
    lines.append(asp.fact("hazard", "tar_walk", "tar"))
    lines.append(asp.fact("thin", "flowers"))
    lines.append(asp.fact("prize", "flowers"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_triples() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show threatened/1."))
    return sorted(set(asp.atoms(model, "threatened")))


def asp_verify() -> int:
    if valid_story_triples():
        print(f"OK: python gate has {len(valid_story_triples())} combo(s).")
        return 0
    print("MISMATCH: no valid combos.")
    return 1


CURATED = [
    StoryParams(place="flower_field", activity="tar_walk", prize="flowers", name="Pip", animal="rabbit", trait="curious", scenario="tipped_pail", telling="clue_first", seed=11),
    StoryParams(place="flower_field", activity="tar_walk", prize="flowers", name="Nia", animal="mouse", trait="gentle", scenario="rain_channel", telling="question_turn", seed=29),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "flower_field":
        raise StoryError("No story: this world only lives in the flower field.")
    if args.activity and args.activity != "tar_walk":
        raise StoryError("No story: only tar-walk belongs here.")
    if args.prize and args.prize != "flowers":
        raise StoryError("No story: only the thin flowers are part of this world.")
    if args.name is None and args.animal is None:
        name, animal = rng.choice(ANIMALS)
    elif args.name is not None and args.animal is None:
        name = args.name
        animal = next((kind for known_name, kind in ANIMALS if known_name == name), rng.choice(ANIMALS)[1])
    elif args.name is None:
        animal = args.animal
        name = next((known_name for known_name, kind in ANIMALS if kind == animal), rng.choice(ANIMALS)[0])
    else:
        name, animal = args.name, args.animal
    return StoryParams(
        place="flower_field",
        activity="tar_walk",
        prize="flowers",
        name=name,
        animal=animal,
        trait=args.trait or rng.choice(TRAITS),
        scenario=args.scenario or rng.choice(sorted(INCIDENTS)),
        telling=args.telling or rng.choice(TELLINGS),
    )


def generate(params: StoryParams) -> StorySample:
    scenario = params.scenario or "tipped_pail"
    telling = params.telling or "clue_first"
    detail_seed = params.seed if params.seed is not None else sum(ord(ch) for ch in f"{params.name}:{scenario}:{telling}")
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.animal,
        params.trait,
        INCIDENTS[scenario],
        telling,
        random.Random(detail_seed ^ 0x5A17),
    )
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show threatened/1."))
        return
    if args.asp:
        print("1 compatible story triple:")
        print("  flower_field tar_walk flowers")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
