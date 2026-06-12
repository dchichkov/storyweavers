#!/usr/bin/env python3
"""
Cautionary Tales Generator
Generates unique scripted cautionary tales for young children.
Pure Python implementation with no external dependencies.
"""

import random
import itertools
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Seed for reproducibility (can be commented out for random generation)
# random.seed(42)

# =============================================================================
# CHARACTER DATA
# =============================================================================

BOY_NAMES = [
    "Tim", "Tommy", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli",
    "Luke", "Jake", "Ryan", "Adam", "Owen", "Ethan", "Liam", "Cole", "Drew", "Zach",
    "Milo", "Theo", "Henry", "Oscar", "Felix", "Hugo", "Jasper", "Archie", "Alfie", "Charlie"
]

GIRL_NAMES = [
    "Lily", "Emma", "Mia", "Zoe", "Ava", "Ella", "Ruby", "Lucy", "Ivy", "Chloe",
    "Anna", "Sara", "Maya", "Nina", "Leah", "Rose", "Daisy", "Bella", "Nora", "Iris",
    "Hazel", "Violet", "Luna", "Stella", "Olive", "Pearl", "Clara", "Flora", "Lydia", "Sophie"
]

PET_NAMES = [
    "Spot", "Buddy", "Max", "Whiskers", "Fluffy", "Patches", "Lucky", "Coco",
    "Biscuit", "Muffin", "Teddy", "Ginger", "Shadow", "Pepper", "Cookie", "Oreo"
]

ANIMAL_TYPES = ["dog", "cat", "bunny", "bird", "hamster", "goldfish", "turtle", "frog"]

FAMILY_MEMBERS = ["mom", "dad", "mommy", "daddy", "grandma", "grandpa"]

# =============================================================================
# SETTINGS AND OBJECTS
# =============================================================================

OUTDOOR_LOCATIONS = [
    "the park", "the garden", "the backyard", "the playground", "the meadow",
    "the beach", "the forest", "the woods", "the field", "the pond"
]

INDOOR_LOCATIONS = [
    "the kitchen", "the living room", "the bedroom", "their room", "the house",
    "the playroom", "the attic", "the basement", "the hallway", "the garage"
]

PUBLIC_PLACES = [
    "the store", "the market", "the mall", "the library", "the museum",
    "the zoo", "the fair", "the circus", "the school", "the bakery"
]

WEATHER_CONDITIONS = [
    "sunny", "rainy", "windy", "cloudy", "stormy", "snowy", "foggy", "warm", "cold"
]

TOYS = [
    "toy car", "doll", "ball", "teddy bear", "blocks", "puzzle", "kite",
    "train set", "toy boat", "jump rope", "balloon", "yo-yo", "toy truck",
    "stuffed animal", "action figure", "toy plane", "building blocks", "spinning top"
]

FOOD_ITEMS = [
    "cookies", "cake", "candy", "ice cream", "chocolate", "cupcakes", "pie",
    "fruit", "apples", "berries", "sandwiches", "crackers", "juice", "milk"
]

DANGEROUS_THINGS = [
    "a sharp knife", "hot stove", "deep water", "tall tree", "busy road",
    "electrical outlet", "medicine bottle", "cleaning supplies", "matches",
    "broken glass", "a steep hill", "thin ice", "a strange dog", "a dark cave"
]

SIMPLE_OBJECTS = [
    "a shiny rock", "a colorful leaf", "a pretty flower", "a stick",
    "a butterfly", "a ladybug", "a feather", "a seashell", "an acorn",
    "a pinecone", "a smooth pebble", "a caterpillar", "a snail", "a worm"
]

# =============================================================================
# TRAITS AND EMOTIONS
# =============================================================================

POSITIVE_TRAITS = [
    "kind", "brave", "curious", "playful", "happy", "friendly", "helpful",
    "clever", "gentle", "caring", "cheerful", "sweet", "loving", "joyful"
]

NEGATIVE_TRAITS = [
    "stubborn", "impatient", "careless", "greedy", "selfish", "reckless",
    "disobedient", "jealous", "naughty", "lazy", "hasty", "proud", "vain"
]

EMOTIONS = [
    "happy", "sad", "scared", "angry", "excited", "worried", "surprised",
    "confused", "proud", "ashamed", "lonely", "jealous", "grateful", "sorry"
]

# =============================================================================
# ACTIONS AND CONSEQUENCES
# =============================================================================

FORBIDDEN_ACTIONS = [
    "touch it", "go there", "take it", "eat it", "play with it",
    "climb it", "open it", "break it", "hide it", "throw it"
]

BAD_OUTCOMES = [
    "fell and got hurt", "got lost", "broke something precious",
    "made someone cry", "got sick", "lost a friend", "was grounded",
    "couldn't play anymore", "had to go home early", "missed the fun",
    "got in trouble", "made a big mess", "scared someone", "hurt themselves"
]

GOOD_OUTCOMES = [
    "learned an important lesson", "said sorry and was forgiven",
    "made things right", "helped fix the problem", "became more careful",
    "promised to listen next time", "hugged and made up", "shared with others"
]

# =============================================================================
# MORAL LESSONS
# =============================================================================

LESSONS = [
    "always listen to your parents",
    "be careful with things that are not yours",
    "share with others",
    "tell the truth, even when it's hard",
    "think before you act",
    "be kind to animals",
    "don't take things without asking",
    "patience is important",
    "it's okay to ask for help",
    "be gentle with others",
    "follow the rules to stay safe",
    "saying sorry can fix things",
    "be grateful for what you have",
    "don't be greedy",
    "treat others how you want to be treated",
    "listen to warnings from grown-ups",
    "being honest is always best",
    "taking turns makes everyone happy",
    "some things are not meant for playing",
    "it's important to be patient",
    "don't talk to strangers",
    "stay close to your family in new places",
    "some things are dangerous and should be avoided",
    "actions have consequences",
    "being selfish can hurt others"
]

# =============================================================================
# STORY TEMPLATES
# =============================================================================

@dataclass
class Character:
    name: str
    gender: str  # 'boy' or 'girl'
    trait: str
    
    @property
    def pronoun(self) -> str:
        return "he" if self.gender == "boy" else "she"
    
    @property
    def pronoun_obj(self) -> str:
        return "him" if self.gender == "boy" else "her"
    
    @property
    def pronoun_poss(self) -> str:
        return "his" if self.gender == "boy" else "her"
    
    @property
    def pronoun_reflex(self) -> str:
        return "himself" if self.gender == "boy" else "herself"
    
    @property
    def title(self) -> str:
        return "little boy" if self.gender == "boy" else "little girl"


def create_random_character(gender: Optional[str] = None) -> Character:
    """Create a random character."""
    if gender is None:
        gender = random.choice(["boy", "girl"])
    
    if gender == "boy":
        name = random.choice(BOY_NAMES)
    else:
        name = random.choice(GIRL_NAMES)
    
    trait = random.choice(POSITIVE_TRAITS + NEGATIVE_TRAITS)
    return Character(name, gender, trait)


def create_sibling(main_char: Character) -> Character:
    """Create a sibling character with opposite gender."""
    other_gender = "girl" if main_char.gender == "boy" else "boy"
    return create_random_character(other_gender)


# =============================================================================
# STORY GENERATORS - Each generates a different type of cautionary tale
# =============================================================================

def generate_disobedience_story(char: Character) -> str:
    """Story about a child who doesn't listen to their parent."""
    location = random.choice(OUTDOOR_LOCATIONS + INDOOR_LOCATIONS)
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    dangerous_thing = random.choice(DANGEROUS_THINGS)
    bad_outcome = random.choice(BAD_OUTCOMES)
    
    warning_phrases = [
        f"told {char.pronoun_obj} not to go near {dangerous_thing}",
        f"warned {char.pronoun_obj} to stay away from {dangerous_thing}",
        f"said {char.pronoun} should never touch {dangerous_thing}",
        f"reminded {char.pronoun_obj} that {dangerous_thing} was dangerous"
    ]
    warning = random.choice(warning_phrases)
    
    story = f"""Once upon a time, there was a {char.trait} {char.title} named {char.name}. {char.name} loved to play in {location}. One day, {char.pronoun_poss} {parent} {warning}.

{char.name} said, "Okay, {parent}!" But {char.pronoun} was very curious. When {parent} wasn't looking, {char.name} went close to {dangerous_thing}. {char.pronoun.capitalize()} thought it would be fun to explore.

But something bad happened. {char.name} {bad_outcome}. {char.pronoun.capitalize()} started to cry and called for {char.pronoun_poss} {parent}. {parent.capitalize()} came running and helped {char.pronoun_obj}.

{char.name} felt very sorry. {char.pronoun.capitalize()} hugged {char.pronoun_poss} {parent} and said, "I'm sorry I didn't listen." {parent.capitalize()} said, "I told you because I love you and want you to be safe."

From that day on, {char.name} learned that {char.pronoun} should always listen to {char.pronoun_poss} {parent}. Some rules are there to keep us safe."""
    
    return story


def generate_sharing_story(char: Character) -> str:
    """Story about learning to share."""
    sibling = create_sibling(char)
    toy = random.choice(TOYS)
    location = random.choice(INDOOR_LOCATIONS + ["the backyard", "the park"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} had a favorite {toy} that {char.pronoun} loved very much. {char.pronoun.capitalize()} played with it every day.

One day, {char.pronoun_poss} little {"brother" if sibling.gender == "boy" else "sister"} {sibling.name} came and asked, "Can I play with your {toy}?" But {char.name} said, "No! It's mine! Go away!"

{sibling.name} was very sad and started to cry. {char.name} kept playing alone, but it didn't feel fun anymore. {char.pronoun.capitalize()} saw how sad {sibling.name} was and felt bad inside.

Finally, {char.name} went to {sibling.name} and said, "I'm sorry. We can play together." {sibling.name}'s face lit up with a big smile. They played with the {toy} together and had so much more fun!

{char.name} learned that sharing makes everyone happy. When we share, we make more friends and have more fun."""
    
    return story


def generate_curiosity_danger_story(char: Character) -> str:
    """Story about curiosity leading to danger."""
    location = random.choice(OUTDOOR_LOCATIONS)
    dangerous_thing = random.choice([
        "a deep pond", "a tall tree", "a dark cave", "a busy street",
        "an old well", "a steep cliff", "a frozen lake", "a rushing river"
    ])
    parent = random.choice(FAMILY_MEMBERS)
    
    story = f"""Once upon a time, a {char.trait} {char.title} named {char.name} went to {location} with {char.pronoun_poss} {parent}. {char.name} loved to explore and discover new things.

While walking, {char.name} saw {dangerous_thing}. It looked exciting! {char.pronoun.capitalize()} forgot what {char.pronoun_poss} {parent} said about staying close. {char.name} ran toward it to take a closer look.

"Stop!" yelled {char.pronoun_poss} {parent}. But {char.name} got too close and almost fell in! {char.pronoun_poss.capitalize()} {parent} grabbed {char.pronoun_obj} just in time.

{char.name}'s heart was beating fast. {char.pronoun.capitalize()} was very scared. "{parent.capitalize()}, I'm sorry," {char.name} said with tears in {char.pronoun_poss} eyes.

{char.pronoun_poss.capitalize()} {parent} hugged {char.name} tight. "I'm glad you're safe. Some places are dangerous, and that's why we must be careful." {char.name} promised to always listen and never wander off again."""
    
    return story


def generate_lying_story(char: Character) -> str:
    """Story about telling lies and the consequences."""
    broken_item = random.choice([
        "mom's favorite vase", "dad's special mug", "grandma's old clock",
        "the family photo frame", "mom's pretty bowl", "dad's reading glasses"
    ])
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. One day, while playing in {random.choice(INDOOR_LOCATIONS)}, {char.name} accidentally knocked over {broken_item}. It fell to the floor and broke!

{char.name} was very scared. When {parent} came and asked what happened, {char.name} said, "I didn't do it! Maybe the wind did it!" But there was no wind inside the house.

{parent.capitalize()} looked at {char.name} with sad eyes. "Are you telling me the truth?" {char.name} looked at the floor and didn't say anything. {char.pronoun.capitalize()} felt bad for lying.

Finally, {char.name} said, "I'm sorry, {parent}. I did it. I was playing too rough and it was an accident. I was scared to tell you."

{parent.capitalize()} hugged {char.name} and said, "Thank you for telling the truth. Accidents happen, and I'm not angry. But lying makes things worse. Always tell the truth, even when you're scared." {char.name} felt much better after being honest."""
    
    return story


def generate_stranger_danger_story(char: Character) -> str:
    """Story about not talking to strangers."""
    location = random.choice(["the park", "the playground", "the store", "the mall"])
    parent = random.choice(FAMILY_MEMBERS)
    
    story = f"""Once upon a time, a {char.title} named {char.name} went to {location} with {char.pronoun_poss} {parent}. They were having a nice day together.

While {char.pronoun_poss} {parent} was looking at something, a stranger came up to {char.name}. The stranger smiled and said, "Would you like some candy? Come with me!"

{char.name} remembered what {char.pronoun_poss} {parent} had taught {char.pronoun_obj}. {char.pronoun.capitalize()} said loudly, "No! I don't talk to strangers!" Then {char.name} ran back to {char.pronoun_poss} {parent}.

{char.name} told {char.pronoun_poss} {parent} what happened. {parent.capitalize()} was so proud! "You did the right thing! Never go anywhere with someone you don't know."

{char.name} felt brave and safe. {char.pronoun.capitalize()} learned that it's always okay to say no to strangers and run to a grown-up you trust."""
    
    return story


def generate_greed_story(char: Character) -> str:
    """Story about being greedy."""
    food = random.choice(FOOD_ITEMS)
    parent = random.choice(["mom", "dad"])
    sibling = create_sibling(char)
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. One day, {char.pronoun_poss} {parent} made delicious {food} for {char.name} and {char.pronoun_poss} little {"brother" if sibling.gender == "boy" else "sister"} {sibling.name}.

{parent.capitalize()} put the {food} on the table. "Make sure you share nicely," said {parent}. But {char.name} wanted all the {food} for {char.pronoun_reflex}!

When {sibling.name} wasn't looking, {char.name} took most of the {food}. {char.pronoun.capitalize()} ate and ate until {char.pronoun_poss} tummy hurt very much!

{char.name} felt sick and couldn't play anymore. {sibling.name} was sad because there wasn't enough {food} left. {parent.capitalize()} came and saw what happened.

"Being greedy doesn't make you happy," said {parent}. "Now you don't feel good, and {sibling.name} is sad." {char.name} said sorry to {sibling.name} and learned that being greedy only makes everyone feel bad."""
    
    return story


def generate_pet_care_story(char: Character) -> str:
    """Story about being responsible with pets."""
    pet_name = random.choice(PET_NAMES)
    animal = random.choice(["puppy", "kitten", "bunny", "hamster"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name} who had a little {animal} named {pet_name}. {char.name} loved {pet_name} very much.

One day, {char.name} was supposed to give {pet_name} food and water. But {char.name} was busy playing with toys and said, "I'll do it later!"

Later came and went, but {char.name} forgot all about {pet_name}. The little {animal} got very hungry and thirsty. {pet_name} made sad little sounds.

{char.name}'s {random.choice(['mom', 'dad'])} said, "Did you feed {pet_name}?" {char.name} suddenly remembered and felt very bad. {char.pronoun.capitalize()} ran to feed and give water to the {animal}.

"{pet_name} depends on you," said {char.pronoun_poss} parent. "Pets need us to take care of them." {char.name} promised to always remember to care for {pet_name} first, because pets are family too."""
    
    return story


def generate_jealousy_story(char: Character) -> str:
    """Story about dealing with jealousy."""
    sibling = create_sibling(char)
    new_item = random.choice([
        "a new toy", "a pretty dress", "a cool hat", "a fun game",
        "a shiny bike", "beautiful shoes", "a special book"
    ])
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} had a {"brother" if sibling.gender == "boy" else "sister"} named {sibling.name}. One day, {sibling.name} got {new_item} as a present.

{char.name} felt jealous. "Why did {sibling.name} get something and I didn't?" {char.pronoun} thought. {char.name} got so angry that {char.pronoun} took the {new_item.replace('a ', '').replace('an ', '')} and hid it!

{sibling.name} couldn't find {sibling.pronoun_poss} new thing and started to cry. {parent.capitalize()} asked, "{char.name}, do you know where it is?"

{char.name} felt bad seeing {sibling.name} so sad. {char.pronoun.capitalize()} went and got the {new_item.replace('a ', '').replace('an ', '')} and said, "I'm sorry. I took it because I was jealous."

{parent.capitalize()} explained, "Everyone gets different things at different times. {sibling.name}'s special day will be your special day another time." {char.name} hugged {sibling.name} and learned that jealousy only makes everyone sad."""
    
    return story


def generate_patience_story(char: Character) -> str:
    """Story about being patient."""
    waiting_for = random.choice([
        "birthday cake", "a turn on the swing", "a yummy treat",
        "to open presents", "to go to the park", "to watch a movie"
    ])
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} was very excited about {waiting_for}. But {char.pronoun_poss} {parent} said {char.pronoun} had to wait.

"I don't want to wait! I want it now!" said {char.name}. {char.pronoun.capitalize()} started to stomp {char.pronoun_poss} feet and whine.

But being impatient didn't help. It just made {char.name} feel worse. {char.pronoun_poss} {parent} said, "Being upset won't make time go faster."

{char.name} tried to be patient. {char.pronoun.capitalize()} played with toys and helped {char.pronoun_poss} {parent}. Before {char.name} knew it, it was time!

"Waiting wasn't so bad!" said {char.name} with a big smile. {char.pronoun.capitalize()} learned that being patient and finding fun things to do makes waiting easier. Good things come to those who wait!"""
    
    return story


def generate_helping_story(char: Character) -> str:
    """Story about helping others."""
    person_helped = random.choice([
        "an old lady with heavy bags", "a little kid who fell down",
        "a friend who lost a toy", "mom with the dishes",
        "dad in the garden", "a sad classmate"
    ])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. One day, {char.name} saw {person_helped}. At first, {char.name} just wanted to keep playing.

But then {char.name} thought, "What if that was me? I would want someone to help!" So {char.name} went over and asked, "Can I help you?"

The person smiled big and said, "Yes, please! That's so kind of you!" {char.name} helped as best as {char.pronoun} could.

When it was done, the person said, "Thank you so much! You are a wonderful helper!" {char.name} felt so happy inside, happier than when playing alone.

{char.pronoun_poss.capitalize()} {random.choice(['mom', 'dad'])} said, "I'm so proud of you for helping!" {char.name} learned that helping others makes everyone feel good, especially yourself."""
    
    return story


def generate_tantrum_story(char: Character) -> str:
    """Story about throwing tantrums."""
    wanted_thing = random.choice([
        "a toy at the store", "more candy", "to stay up late",
        "to skip bath time", "another cookie", "a new game"
    ])
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. One day, {char.name} really wanted {wanted_thing}. But {char.pronoun_poss} {parent} said no.

{char.name} got very angry! {char.pronoun.capitalize()} started to scream and cry and kick {char.pronoun_poss} feet. {char.pronoun.capitalize()} threw a big tantrum right there!

But the tantrum didn't work. {char.pronoun_poss} {parent} waited until {char.name} calmed down. "Screaming won't change my answer," said {parent}.

{char.name} was tired from all the crying. {char.pronoun.capitalize()} felt silly. The tantrum didn't get {char.pronoun_obj} what {char.pronoun} wanted. It just made {char.pronoun_obj} tired and sad.

{char.name} learned that throwing tantrums doesn't help. It's better to use words and accept when the answer is no. Sometimes grown-ups know what's best."""
    
    return story


def generate_rushing_story(char: Character) -> str:
    """Story about not rushing and being careful."""
    activity = random.choice([
        "running down the stairs", "riding a bike too fast",
        "running by the pool", "skating without looking",
        "climbing too quickly", "jumping on the bed"
    ])
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} was always in a hurry. {char.pronoun.capitalize()} never wanted to slow down!

One day, {char.pronoun_poss} {parent} said, "Be careful! Don't go so fast!" But {char.name} didn't listen. {char.pronoun.capitalize()} was {activity}, going faster and faster.

Suddenly, {char.name} tripped and fell! {char.pronoun.capitalize()} scraped {char.pronoun_poss} knee and it hurt a lot. {char.name} started to cry.

{char.pronoun_poss.capitalize()} {parent} came and put a bandage on the scrape. "This is why I asked you to slow down," said {parent} gently.

{char.name}'s knee hurt for several days. {char.pronoun.capitalize()} learned that rushing can lead to accidents. It's better to slow down and be careful than to get hurt."""
    
    return story


def generate_lost_story(char: Character) -> str:
    """Story about wandering off and getting lost."""
    location = random.choice(["the mall", "the store", "the fair", "the zoo", "the market"])
    parent = random.choice(FAMILY_MEMBERS)
    
    story = f"""Once upon a time, a {char.title} named {char.name} went to {location} with {char.pronoun_poss} {parent}. There were so many exciting things to see!

{char.name} saw something shiny and colorful. Without thinking, {char.pronoun} walked toward it, leaving {char.pronoun_poss} {parent} behind. {char.name} walked and walked until...

{char.pronoun.capitalize()} looked around and didn't see {char.pronoun_poss} {parent} anywhere! {char.name} was lost! {char.pronoun.capitalize()} felt very scared and started to cry.

A kind worker found {char.name} and helped find {char.pronoun_poss} {parent}. When they were together again, {char.name} hugged {char.pronoun_poss} {parent} so tight!

"Never wander off without me," said {parent}. {char.name} learned to always stay close to {char.pronoun_poss} {parent} in busy places. It's scary to be lost."""
    
    return story


def generate_broken_promise_story(char: Character) -> str:
    """Story about keeping promises."""
    friend_name = random.choice(BOY_NAMES + GIRL_NAMES)
    while friend_name == char.name:
        friend_name = random.choice(BOY_NAMES + GIRL_NAMES)
    activity = random.choice([
        "play together at the park", "share their toys",
        "have a tea party", "build a sandcastle",
        "play dress-up", "have a picnic"
    ])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} had a friend named {friend_name}. They promised to {activity} the next day.

But when the next day came, {char.name} decided to do something else instead. {char.pronoun.capitalize()} forgot all about the promise to {friend_name}.

{friend_name} waited and waited, but {char.name} never came. {friend_name} felt very sad and disappointed. When {char.name} saw {friend_name} later, {friend_name} was crying.

"You promised!" said {friend_name}. {char.name} suddenly remembered and felt terrible. "I'm so sorry," said {char.name}. "I forgot."

{char.name} learned that promises are very important. When we break a promise, we hurt our friends. From then on, {char.name} always kept {char.pronoun_poss} promises."""
    
    return story


def generate_fighting_story(char: Character) -> str:
    """Story about fighting and using words instead."""
    sibling = create_sibling(char)
    fight_over = random.choice([
        "a toy", "the TV remote", "the last cookie",
        "who sits in the front", "whose turn it was", "a book"
    ])
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name} who had a {"brother" if sibling.gender == "boy" else "sister"} named {sibling.name}. One day, they both wanted {fight_over}.

"It's mine!" yelled {char.name}. "No, it's mine!" yelled {sibling.name}. They started pushing and grabbing. Soon they were really fighting!

{parent.capitalize()} heard the noise and came in. "Stop!" said {parent}. "Fighting is not okay!" Both {char.name} and {sibling.name} were in trouble.

They had to sit in time-out and think about what they did. {parent.capitalize()} said, "Use your words, not your hands. Talk about problems."

{char.name} and {sibling.name} said sorry to each other. They learned to take turns and talk instead of fight. Using words is much better than fighting!"""
    
    return story


def generate_messy_room_story(char: Character) -> str:
    """Story about keeping things tidy."""
    lost_item = random.choice([
        "favorite toy", "special blanket", "lucky sock",
        "best book", "pet hamster", "beloved teddy bear"
    ])
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} never liked to clean up. {char.pronoun_poss.capitalize()} room was always very messy!

One day, {char.name} couldn't find {char.pronoun_poss} {lost_item}. {char.pronoun.capitalize()} looked everywhere but there was so much stuff on the floor! {char.name} started to cry.

{char.pronoun_poss.capitalize()} {parent} said, "If you kept your room clean, you could find your things." {char.name} knew {parent} was right.

Together, they cleaned the whole room. They picked up toys, folded clothes, and put things in their place. And guess what? They found the {lost_item}!

{char.name} was so happy! {char.pronoun.capitalize()} learned that keeping things clean helps you find what you need. A tidy room is a happy room!"""
    
    return story


def generate_medicine_story(char: Character) -> str:
    """Story about not touching medicine."""
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. One day, {char.name} saw a bottle on the counter. It looked like candy!

{char.name} reached for it, but {char.pronoun_poss} {parent} quickly took it away. "No! That's medicine, not candy!" said {parent}.

"But it looks yummy," said {char.name}. {parent.capitalize()} sat down with {char.name} to explain something important.

"Medicine helps sick people feel better, but it can make healthy people very sick. Only grown-ups can give medicine, and only when someone needs it."

{char.name} understood now. Medicine is not a treat. {char.pronoun.capitalize()} promised to never touch medicine bottles. Some things that look like candy can be dangerous!"""
    
    return story


def generate_screen_time_story(char: Character) -> str:
    """Story about too much screen time."""
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} loved watching cartoons on the TV. {char.pronoun.capitalize()} watched for hours and hours every day.

{char.pronoun_poss.capitalize()} {parent} said, "You watch too much TV. Go play outside!" But {char.name} didn't want to stop.

After many days of too much TV, {char.name}'s head started to hurt. {char.pronoun_poss.capitalize()} eyes felt tired. {char.pronoun.capitalize()} didn't feel good at all.

The doctor said {char.name} needed to rest {char.pronoun_poss} eyes and play more. So {char.name} went outside and discovered how fun it was to run and play!

{char.name} learned that too much TV isn't good for you. Playing outside and using your imagination is much more fun. Now {char.name} only watches a little TV each day."""
    
    return story


def generate_fear_story(char: Character) -> str:
    """Story about facing fears."""
    fear = random.choice([
        "the dark", "dogs", "water", "heights", "loud noises",
        "bugs", "thunder", "the doctor", "trying new things"
    ])
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} was afraid of {fear}. Whenever {char.pronoun} saw {fear}, {char.pronoun} would hide!

One day, {char.pronoun_poss} {parent} said, "Let's try to be brave together." {char.name} was nervous but held {char.pronoun_poss} {parent}'s hand tight.

They faced {fear} slowly and carefully. At first, {char.name} was still scared. But {char.pronoun_poss} {parent} was right there.

Little by little, {char.name} felt less afraid. {char.pronoun.capitalize()} realized that with help, {fear} wasn't so scary after all!

{char.name} was so proud of being brave! {char.pronoun.capitalize()} learned that it's okay to be afraid, but facing your fears makes you stronger. And having someone to help makes it easier."""
    
    return story


def generate_new_friend_story(char: Character) -> str:
    """Story about making new friends."""
    new_friend = create_random_character()
    while new_friend.name == char.name:
        new_friend = create_random_character()
    location = random.choice(["the park", "school", "the playground", "the neighborhood"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. One day at {location}, {char.name} saw a new {new_friend.title} named {new_friend.name}.

At first, {char.name} was too shy to say hello. What if the new kid didn't like {char.pronoun_obj}? {char.name} just watched from far away.

But then {char.name} thought, "Maybe {new_friend.name} wants a friend too!" So {char.name} walked over and said, "Hi! Want to play?"

{new_friend.name}'s face lit up with a big smile. "Yes! I was hoping someone would ask!" They played together and had so much fun!

{char.name} learned that being brave and saying hello can make new friends. Everyone wants to be included. Now {char.name} and {new_friend.name} are best friends!"""
    
    return story


def generate_bedtime_story(char: Character) -> str:
    """Story about the importance of sleep."""
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} never wanted to go to bed. "I'm not tired!" {char.pronoun} always said.

One night, {char.name} stayed up very, very late playing with toys. {char.pronoun_poss.capitalize()} {parent} said, "Time for bed!" But {char.name} hid under the covers and kept playing.

The next day, {char.name} was so tired! {char.pronoun.capitalize()} couldn't run. {char.pronoun.capitalize()} couldn't play. {char.pronoun.capitalize()} fell asleep at breakfast!

{char.pronoun_poss.capitalize()} {parent} said, "This is why we need sleep. Our bodies need rest to play and have fun."

That night, {char.name} went to bed on time. The next day, {char.pronoun} had so much energy! {char.name} learned that sleep helps us feel good and have fun. Now bedtime isn't so bad!"""
    
    return story


def generate_water_safety_story(char: Character) -> str:
    """Story about water safety."""
    water_place = random.choice(["the pool", "the lake", "the beach", "the pond"])
    parent = random.choice(FAMILY_MEMBERS)
    
    story = f"""Once upon a time, a {char.title} named {char.name} went to {water_place} with {char.pronoun_poss} {parent}. It was a hot day and the water looked so inviting!

{char.pronoun_poss.capitalize()} {parent} said, "Wait for me before going in the water." But {char.name} was too excited. {char.pronoun.capitalize()} ran and jumped right in!

The water was deeper than {char.name} thought! {char.pronoun.capitalize()} couldn't touch the bottom and got scared. {char.pronoun.capitalize()} started to splash and cry for help.

{char.pronoun_poss.capitalize()} {parent} quickly jumped in and pulled {char.name} out. They were both very shaken up.

{char.name} learned an important lesson that day. Water can be dangerous! Always wait for a grown-up, and never swim alone. Now {char.name} always asks for permission before going near water."""
    
    return story


def generate_bad_words_story(char: Character) -> str:
    """Story about not using bad words."""
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. One day, {char.name} heard some big kids say a word that sounded funny. So {char.name} said it too!

{char.pronoun_poss.capitalize()} {parent}'s face looked very surprised and sad. "Where did you learn that word?" asked {parent}. "That's a bad word that hurts people's feelings."

{char.name} didn't know! {char.pronoun.capitalize()} just thought it sounded funny. But now {char.pronoun} understood that some words can make people feel bad.

{parent.capitalize()} explained, "Kind words make people happy. Mean words make people sad. We always want to use kind words."

{char.name} felt sorry for saying the bad word. {char.pronoun.capitalize()} learned to think before speaking. Now {char.name} uses kind words that make people smile!"""
    
    return story


def generate_eating_habits_story(char: Character) -> str:
    """Story about healthy eating."""
    junk_food = random.choice(["candy", "chips", "cookies", "soda", "cake"])
    healthy_food = random.choice(["vegetables", "fruits", "carrots", "apples", "broccoli"])
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} only wanted to eat {junk_food}. "I don't like {healthy_food}!" {char.pronoun} would say every day.

{char.pronoun_poss.capitalize()} {parent} tried to give {char.name} healthy food, but {char.name} always said no. {char.pronoun.capitalize()} only ate {junk_food} for days and days.

Soon, {char.name} didn't feel good. {char.pronoun_poss.capitalize()} tummy hurt and {char.pronoun} had no energy to play. The doctor said {char.name} needed to eat healthy food to feel better.

{char.name} tried the {healthy_food}, just a tiny bite. Hey, it wasn't so bad! Actually, it was pretty good! {char.pronoun.capitalize()} tried more healthy foods and started feeling much better.

Now {char.name} eats lots of good food that makes {char.pronoun_obj} strong. {char.pronoun.capitalize()} still has treats sometimes, but {char.pronoun} knows healthy food is important!"""
    
    return story


def generate_taking_turns_story(char: Character) -> str:
    """Story about taking turns."""
    friend = create_random_character()
    while friend.name == char.name:
        friend = create_random_character()
    toy = random.choice(["the swing", "the slide", "a toy", "the ball", "the bike"])
    
    story = f"""Once upon a time, a {char.title} named {char.name} and a {friend.title} named {friend.name} were playing together. They both wanted to use {toy}.

"Me first!" yelled {char.name}. "No, me first!" yelled {friend.name}. They pushed and pulled, and soon they were both very upset.

An older kid saw them fighting and came over. "Why don't you take turns? One person goes, then the other person goes."

{char.name} went first for a little while, then it was {friend.name}'s turn. They kept switching, and guess what? They both got to play!

{char.name} and {friend.name} learned that taking turns is fair. Everyone gets a chance, and no one feels left out. Now they always take turns and never fight!"""
    
    return story


def generate_fire_safety_story(char: Character) -> str:
    """Story about fire safety."""
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. One day, {char.name} saw matches on the table. They looked interesting!

{char.name} reached for the matches, but {char.pronoun_poss} {parent} quickly stopped {char.pronoun_obj}. "No! Those are very dangerous!" said {parent}.

{parent.capitalize()} sat down with {char.name} and explained. "Fire is not a toy. Matches and lighters can start fires that hurt people and burn things."

"If you ever see fire or smoke, you should tell a grown-up right away. And remember: Stop, Drop, and Roll if your clothes catch fire."

{char.name} understood now. Fire is very serious. Only grown-ups can use things that make fire. {char.pronoun.capitalize()} promised to never touch matches or lighters."""
    
    return story


def generate_apologizing_story(char: Character) -> str:
    """Story about saying sorry."""
    friend = create_random_character()
    while friend.name == char.name:
        friend = create_random_character()
    mean_action = random.choice([
        "called them a name", "broke their toy", "didn't share",
        "pushed them", "said something mean", "took their snack"
    ])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. One day, {char.name} {mean_action} to {char.pronoun_poss} friend {friend.name}. {friend.name} was very sad.

At first, {char.name} didn't want to say sorry. {char.pronoun.capitalize()} felt embarrassed and a little stubborn. But {friend.name} wouldn't play with {char.pronoun_obj} anymore.

{char.name}'s {random.choice(['mom', 'dad'])} said, "When we hurt someone, we need to say sorry. It helps fix the hurt."

{char.name} found {friend.name} and said, "I'm really sorry for what I did. It was wrong. Can you forgive me?" {friend.name} smiled and said yes.

They hugged and played together again! {char.name} learned that saying sorry is hard but important. It makes friendships strong and helps everyone feel better."""
    
    return story


def generate_playground_safety_story(char: Character) -> str:
    """Story about playground safety."""
    parent = random.choice(FAMILY_MEMBERS)
    equipment = random.choice(["the monkey bars", "the slide", "the swing", "the climbing wall"])
    
    story = f"""Once upon a time, a {char.title} named {char.name} loved going to the playground. {char.pronoun_poss.capitalize()} favorite thing was {equipment}.

One day, {char.name} wanted to show off. {char.pronoun.capitalize()} climbed higher than {char.pronoun} should and hung upside down in a silly way. "Look at me!" {char.pronoun} yelled.

But then {char.name} lost {char.pronoun_poss} grip and fell! {char.pronoun.capitalize()} hurt {char.pronoun_poss} arm and started to cry. {char.pronoun_poss.capitalize()} {parent} came running.

At the doctor, they said {char.name}'s arm would be okay, but {char.pronoun} had to wear a bandage and rest. {char.name} couldn't play for a whole week!

{char.name} learned that playground rules are there to keep us safe. Showing off and being silly on equipment can lead to getting hurt. Play safe, have fun!"""
    
    return story


def generate_gratitude_story(char: Character) -> str:
    """Story about being grateful."""
    gift = random.choice(["a toy", "a book", "clothes", "a game", "art supplies"])
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. For {char.pronoun_poss} birthday, {char.name} got {gift} from {char.pronoun_poss} {parent}.

But {char.name} wasn't happy. "This isn't what I wanted!" {char.pronoun} complained. "I wanted something else!" {char.pronoun_poss.capitalize()} {parent} looked very sad.

Later, {char.name} saw a child who had no toys at all. That child looked at {char.name}'s {gift.replace('a ', '').replace('an ', '')} and said, "Wow, you're so lucky!"

{char.name} suddenly felt bad for complaining. {char.pronoun.capitalize()} realized that having any gift is special. {char.pronoun_poss.capitalize()} {parent} worked hard to give {char.pronoun_obj} something nice.

{char.name} ran to {char.pronoun_poss} {parent} and said, "Thank you for my gift! I love it!" {char.pronoun.capitalize()} learned to be grateful for what {char.pronoun} has. Being thankful makes everyone happier!"""
    
    return story


def generate_bullying_story(char: Character) -> str:
    """Story about dealing with bullies."""
    bully_name = random.choice(BOY_NAMES + GIRL_NAMES)
    while bully_name == char.name:
        bully_name = random.choice(BOY_NAMES + GIRL_NAMES)
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. At school, a bigger kid named {bully_name} was mean to {char.pronoun_obj}. {bully_name} called {char.name} names and made {char.pronoun_obj} feel sad.

{char.name} didn't want to go to school anymore. {char.pronoun.capitalize()} would cry and feel scared. But {char.pronoun} didn't tell anyone what was happening.

Finally, {char.pronoun_poss} {random.choice(['mom', 'dad'])} noticed something was wrong. {char.name} told them about {bully_name}. Together, they talked to the teacher.

The teacher helped stop the bullying. {bully_name} learned that being mean is wrong. {char.name} learned that it's important to tell grown-ups when someone is being mean.

{char.name} felt safe again! {char.pronoun.capitalize()} learned that telling someone isn't tattling—it's asking for help. We should always speak up when something is wrong!"""
    
    return story


def generate_outdoor_adventure_story(char: Character) -> str:
    """Story about respecting nature."""
    location = random.choice(["the forest", "the beach", "the park", "the hiking trail"])
    parent = random.choice(FAMILY_MEMBERS)
    nature_thing = random.choice([
        "a bird's nest", "a wild animal", "flowers", "a bee hive",
        "a snake", "berries on a bush", "mushrooms"
    ])
    
    story = f"""Once upon a time, a {char.title} named {char.name} went to {location} with {char.pronoun_poss} {parent}. {char.name} loved exploring and seeing all the plants and animals.

While walking, {char.name} saw {nature_thing}. It looked so cool! {char.name} wanted to touch it and take it home.

But {char.pronoun_poss} {parent} said, "Wait! We should only look, not touch. Some things in nature can be dangerous or need to stay where they are."

{parent.capitalize()} explained that touching the wrong things could hurt {char.name} or the animals. "We're just visitors here. We should respect nature."

{char.name} understood. {char.pronoun.capitalize()} took pictures with {char.pronoun_poss} eyes instead of {char.pronoun_poss} hands. Looking is wonderful too! {char.name} learned to enjoy nature safely and respectfully."""
    
    return story


def generate_homework_story(char: Character) -> str:
    """Story about doing homework/responsibilities."""
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    fun_activity = random.choice(["watch TV", "play video games", "play outside", "play with toys"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. After school, {char.name} was supposed to do homework. But {char.pronoun} wanted to {fun_activity} instead!

"I'll do it later!" said {char.name}, running off to play. {char.pronoun_poss.capitalize()} {parent} called, "Remember your homework!" But {char.name} didn't listen.

Later came and went. Before {char.name} knew it, it was bedtime! {char.pronoun.capitalize()} hadn't done any homework. Now it was too late, and {char.pronoun} was very tired.

The next day at school, the teacher was disappointed that {char.name} didn't have {char.pronoun_poss} homework. {char.name} felt embarrassed and sad.

After that, {char.name} learned to do homework first, then play. When you finish your work first, you can play without worrying! Work first, then play—that's the best way!"""
    
    return story


# =============================================================================
# STORY TEMPLATE VARIATIONS
# =============================================================================

def generate_simple_accident_story(char: Character) -> str:
    """Simple story about an accident."""
    # Pair activities with logically related injuries
    activity_injuries = [
        ("running in the house", ["fell down", f"bumped {char.pronoun_poss} head", f"twisted {char.pronoun_poss} ankle", "got a bruise"]),
        ("playing with scissors", [f"cut {char.pronoun_poss} finger", f"hurt {char.pronoun_poss} hand", "got a scrape"]),
        ("jumping on furniture", ["fell down", f"bumped {char.pronoun_poss} head", "got a bruise", f"twisted {char.pronoun_poss} ankle"]),
        ("throwing balls inside", [f"bumped {char.pronoun_poss} head", "broke something and got hurt", "got a bruise"]),
        ("standing on a chair", ["fell down", f"bumped {char.pronoun_poss} head", "got a bruise", f"twisted {char.pronoun_poss} ankle"]),
        ("playing too rough", ["got a scrape", "got a bruise", f"bumped {char.pronoun_poss} head", f"hurt {char.pronoun_poss} arm"]),
    ]
    activity, injuries = random.choice(activity_injuries)
    injury = random.choice(injuries)
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} was {activity}, even though {char.pronoun_poss} {parent} said not to.

While playing, {char.name} {injury}! It hurt a lot and {char.name} started to cry. {char.pronoun_poss.capitalize()} {parent} came running to help.

{parent.capitalize()} cleaned the boo-boo and gave {char.name} a bandage. "This is why I said to be careful," {parent} explained gently.

{char.name} felt better after a hug and a kiss. But {char.pronoun} learned an important lesson: the rules are there to keep {char.pronoun_obj} safe.

From then on, {char.name} remembered to be more careful. Getting hurt is no fun, and following the rules helps avoid accidents!"""
    
    return story


def generate_bad_ending_story(char: Character) -> str:
    """Story with a cautionary bad ending."""
    forbidden_action = random.choice([
        ("eating candy before dinner", "couldn't eat dinner and had a tummy ache all night"),
        ("not wearing a jacket", "caught a cold and had to stay in bed for days"),
        ("running away from parents at the store", "got lost for a very long time"),
        ("not brushing teeth", "got a cavity that hurt very much"),
        ("touching the hot stove", "burned their hand and it hurt for a long time"),
        ("playing too close to the road", "almost got hit by a car and was very scared")
    ])
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    action, consequence = forbidden_action
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. {char.name} didn't like to listen to rules. {char.pronoun.capitalize()} thought rules were boring!

One day, {char.name}'s {parent} said not to do something. But {char.name} didn't listen. {char.pronoun.capitalize()} kept {action} anyway.

Then something bad happened. {char.name} {consequence}. {char.pronoun.capitalize()} wished {char.pronoun} had listened!

{char.name}'s {parent} wasn't angry, just sad. "I told you because I love you and want to keep you safe," {parent} said.

{char.name} finally understood. Rules aren't to be mean—they're to protect us! {char.pronoun.capitalize()} learned that lesson the hard way. Now {char.pronoun} listens more carefully."""
    
    return story


def generate_teamwork_story(char: Character) -> str:
    """Story about working together."""
    friend = create_random_character()
    while friend.name == char.name:
        friend = create_random_character()
    task = random.choice([
        "build a tall tower with blocks", "finish a big puzzle",
        "clean up the playroom", "carry heavy boxes", "make a sandcastle"
    ])
    
    story = f"""Once upon a time, a {char.title} named {char.name} wanted to {task}. {char.pronoun.capitalize()} tried and tried, but it was too hard to do alone!

Then {char.name}'s friend {friend.name} came by. "Need help?" asked {friend.name}. At first, {char.name} said, "No, I can do it myself!"

But after trying more and failing, {char.name} finally said, "Okay, please help me." Together, they started working.

With two people helping, the job became easy! They finished quickly and had so much fun doing it together. They high-fived and celebrated!

{char.name} learned that it's okay to ask for help. Working together makes hard things easier and more fun. Two friends are better than one!"""
    
    return story


def generate_morning_routine_story(char: Character) -> str:
    """Story about morning routine."""
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name}. Every morning, {char.name} didn't want to get up. {char.pronoun.capitalize()} played and dawdled instead of getting ready.

One day, because {char.name} was so slow, {char.pronoun} missed the school bus! {char.pronoun_poss.capitalize()} {parent} had to drive {char.pronoun_obj}, and they were both late.

At school, {char.name} had missed story time, the best part of the day! {char.pronoun.capitalize()} was so sad. {char.pronoun_poss.capitalize()} friends had all the fun without {char.pronoun_obj}.

That night, {char.pronoun_poss} {parent} helped make a list: wake up, brush teeth, get dressed, eat breakfast. {char.name} put stickers on the list when {char.pronoun} finished each thing.

The next day, {char.name} got ready quickly! {char.pronoun.capitalize()} caught the bus and didn't miss anything. Having a routine makes mornings easier and better!"""
    
    return story


def generate_toy_care_story(char: Character) -> str:
    """Story about taking care of belongings."""
    toy = random.choice(TOYS)
    parent = random.choice(["mom", "dad", "mommy", "daddy"])
    
    story = f"""Once upon a time, there was a {char.title} named {char.name} who had a special {toy}. It was {char.pronoun_poss} favorite toy in the whole world!

But {char.name} didn't take good care of it. {char.pronoun.capitalize()} left it outside in the rain, threw it around, and never put it away nicely.

One day, the {toy} broke! A piece fell off and it didn't work anymore. {char.name} was so sad and cried. {char.pronoun.capitalize()} wanted {char.pronoun_poss} favorite toy back!

{char.pronoun_poss.capitalize()} {parent} said, "If you had taken better care of it, it might not have broken. Things need love and care."

{char.name} learned to take care of {char.pronoun_poss} things. {char.pronoun.capitalize()} puts toys away nicely now and treats them gently. Taking care of our things makes them last longer!"""
    
    return story


# =============================================================================
# MAIN STORY GENERATOR
# =============================================================================

# List of all story generator functions
STORY_GENERATORS = [
    generate_disobedience_story,
    generate_sharing_story,
    generate_curiosity_danger_story,
    generate_lying_story,
    generate_stranger_danger_story,
    generate_greed_story,
    generate_pet_care_story,
    generate_jealousy_story,
    generate_patience_story,
    generate_helping_story,
    generate_tantrum_story,
    generate_rushing_story,
    generate_lost_story,
    generate_broken_promise_story,
    generate_fighting_story,
    generate_messy_room_story,
    generate_medicine_story,
    generate_screen_time_story,
    generate_fear_story,
    generate_new_friend_story,
    generate_bedtime_story,
    generate_water_safety_story,
    generate_bad_words_story,
    generate_eating_habits_story,
    generate_taking_turns_story,
    generate_fire_safety_story,
    generate_apologizing_story,
    generate_playground_safety_story,
    generate_gratitude_story,
    generate_bullying_story,
    generate_outdoor_adventure_story,
    generate_homework_story,
    generate_simple_accident_story,
    generate_bad_ending_story,
    generate_teamwork_story,
    generate_morning_routine_story,
    generate_toy_care_story,
]


def generate_unique_stories(count: int = 500) -> List[str]:
    """Generate a specified number of unique cautionary tales."""
    stories = []
    seen_stories = set()
    
    # Create a variety of characters to cycle through
    all_names = [(name, "boy") for name in BOY_NAMES] + [(name, "girl") for name in GIRL_NAMES]
    
    attempts = 0
    max_attempts = count * 3  # Allow for retries
    
    while len(stories) < count and attempts < max_attempts:
        attempts += 1
        
        # Pick a random generator and character
        generator = random.choice(STORY_GENERATORS)
        name, gender = random.choice(all_names)
        trait = random.choice(POSITIVE_TRAITS + NEGATIVE_TRAITS)
        char = Character(name, gender, trait)
        
        # Generate the story
        story = generator(char)
        
        # Clean up whitespace
        story = '\n'.join(line.strip() for line in story.strip().split('\n'))
        
        # Check for uniqueness (use hash of first 100 chars + last 100 chars)
        story_hash = hash(story[:200] + story[-200:] if len(story) > 400 else story)
        
        if story_hash not in seen_stories:
            seen_stories.add(story_hash)
            stories.append(story)
    
    return stories


def main():
    """Main function to generate and print cautionary tales."""
    stories = generate_unique_stories(1000)
    
    # Print all stories separated by four newlines
    print("\n\n\n\n".join(stories))


if __name__ == "__main__":
    main()

