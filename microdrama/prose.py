"""Encounter-scale discourse plans. Only committed episode snapshots are rendered.

Paragraphs are authored performances, selected by enacted outcomes. This layer
does not update state, invent missing transitions, or paraphrase a trace with an LLM.
Incidental gestures are literary texture; consequential propositions are traced.
"""
from dataclasses import dataclass

from .engine import StoryError


@dataclass
class Paragraph:
    id: str
    drama: str
    text: str
    evidence: list[str]
    reveals: list[str]


def render(ep, params):
    b, s, name = ep.before, ep.after, ep.id
    revealed = []
    if name == "opening":
        text = '''At the edge of the forest, the Three Little Pigs built houses and waited to be admired. The first used straw, the second wood, and the third enough bricks to make him feel sensible. None paid much attention to what lay beneath the walls.

Across the creek, G. Wolf lived in a gray stone cottage with a level floor and a stove that drew well. In the evening he made fish soup with dill. Mira and Tansy, two young pigs from the market, sometimes smelled it on their way home. They knew very little about their neighbor. They knew a great deal about wolves in stories.'''
        revealed = ["cottage.owner", "cottage.occupant"]
    elif name == "wind":
        text = '''The first strong wind pulled the straw house apart. Its owner stood among the scattered bundles with straw in his ears.

“G. Wolf blew it down,” he announced.

“I heard him laughing,” said his brother, who had heard the wind.

The Third Little Pig hesitated. Then he saw the neighbors waiting for him to nod, and nodded. A wicked wolf was easier to explain than a weak house. By supper they had told the story often enough to stop mentioning the weather.'''
        revealed = ["straw.cause", "straw.failed"]
    elif name == "market":
        text = '''The pigs printed a poster. Its wolf had red eyes and a mouth large enough to swallow a roof. They nailed it beside the market scales, where everyone had to wait.

Mira read it to Tansy. Tansy repeated it to the next pig in line. Neither had seen the house fall, but both began watching the creek path.

The baker no longer called Wolf over for a chat. Children were pulled away from his gate. The same paper that said he was dangerous told the young pigs to report anything suspicious. It was a small sheet. It managed to stand between a great many neighbors.'''
        revealed = ["poster.printed", "mira.meme.BlameWolf", "tansy.meme.BlameWolf", "valley.reporting"]
    elif name == "exile":
        text = '''One morning before the market opened, Wolf packed his pot, his spoon, and his dried dill. He left the cottage empty and followed the creek until it became a river, then followed the river to the sea.

On the rocky shore he could hear water instead of whispers. He made no houses fall there. Back in the valley, the poster stayed on its tree. It no longer needed him to be present.'''
        revealed = ["wolf.location", "cottage.occupant"]
    elif name == "rain":
        text = '''Heavy rain softened the ground beneath the wooden house. One corner sank; the rest followed it sideways into the mud.

“He has done it again,” said the Second Little Pig.

“From the sea?” someone asked.

“Why else would he have run away?”

The pigs bought a printing press. Their newspaper made flight into proof and mud into a detail too dull to print. Young pigs learned which questions earned praise. Questions about wolves were welcome. Questions about foundations were less so.'''
        revealed = ["wood.cause", "newspaper.printed"]
    elif name == "occupation":
        text = '''Then a crack opened in the brick house. Its walls were heavy; its footing was poor. The Third Little Pig put a picture over the crack, but the picture would not lie flat.

The brothers agreed that three accidents could hardly be an accident. They moved into Wolf's cottage, with its good light and straight walls. It still belonged to Wolf. That did not prevent the pigs from sleeping in it.

For a little while, owning the loudest story seemed almost as useful as owning the house.'''
        revealed = ["brick.cause", "cottage.owner", "cottage.occupant"]
    elif name == "return":
        text = '''Whispers began about the pigs living in a wolf's house. The brothers decided the valley needed its villain back where everyone could see him.

They found Wolf on the shore. He was old, and there were three of them. They brought him home to the cracked brick house and required him to build cottages for the young pigs. He measured the ground, laid firm stones, and showed the workers how to use a level.

“Look what we have built,” the brothers told the newspaper. Wolf went on measuring. The new cottages were sound. The story attached to them was not.'''
        revealed = ["wolf.coerced", "wolf.location", "pigs.claims_authorship", "valley.cottages_built"]
    elif name == "fox":
        text = '''Story Fox arrived while Wolf was setting out another foundation. The watch list had a place for wolves and no place for foxes. She studied the poster, then the unattended lunch baskets.

By noon, three portions of cheese had disappeared into her mouth.'''
        if s["mira.saw_theft"]:
            text += '''

Mira saw the red tail under the bench. “That wasn't Wolf,” she told Tansy. She could no longer make herself believe this theft belonged to him. Tansy had been carrying bricks and had seen nothing.

The brothers blamed Wolf anyway. Mira watched them point toward a worker whose paws had been full of stone.'''
        else:
            text += '''

Mira and Tansy had been carrying bricks; neither saw her take it. “It must be Wolf,” they said. The brothers agreed, and promised tighter rules. Fox licked her whiskers behind the baskets. Nobody searched beneath the red tail.'''
        revealed = ["fox.took_cheese", "mira.saw_theft", "pigs.blame_cheese", "cheese.portions"]
    elif name == "whisper":
        text = '''Fox heard a new name in the work gangs: the Three Little Wolves. She carried it to the cottage by the creek.

“Such a fine wolf's house,” she told the brothers. “The young pigs say you have become quite at home in it.”

“We are pigs,” said the First Little Pig.

“Naturally.” Fox looked up at the stonework. “Though a house can tell a story of its own.”

That night the brothers looked at their comfortable walls as if the walls had grown fur. They wanted a building that would settle who they were. Fox wanted another reason to stay near the lunch baskets.'''
        revealed = ["valley.whispers", "pigs.meme.StatusThreat"]
    elif name == "commission":
        text = '''“A palace,” said the Third Little Pig. “On the hill. With a tower.”

Fox suggested books. Famous palaces had plans, she explained; a truly important palace ought to have important plans. The pigs ordered wagons of them. Wolf turned one upside-down volume the right way up and went to examine the hill.

Mira and Tansy carried stone. Wolf laid out the rooms. Between the windows they built shelves for books about foundations, bridges, roofs, and water.'''
        if s["books.accessible"]:
            text += ''' The pigs left the shelves open so that visitors would admire the collection. They had bought the books to be seen. They did not think very hard about being read.'''
        else:
            text += ''' The pigs ordered cupboard doors fitted over the shelves and kept them locked. Visitors could admire the titles through wire fronts. Mira pulled once at a handle; the books stayed beyond her reach.'''
        if s["valley.work_arrangement"] == "shared":
            text += '''

The two young pigs were assigned to work together. They learned the small signals that meant lift, hold, and wait.'''
        else:
            text += '''

The brothers assigned the young pigs to separate jobs. Each answered to a different overseer; their breaks rarely overlapped.'''
        revealed = ["books.accessible", "books.delivered", "pigs.commission"]
    elif name.startswith("read_"):
        child = name[5:]
        if child == "mira":
            text = '''Mira took down the foundations book. One drawing showed water gathering against a wall; another showed it running away through a shallow channel. She recognized the first picture. Her own doorstep looked like that whenever it rained.

“Where would the water go here?” she murmured, tracing the channel with a dusty hoof.'''
        else:
            text = '''Tansy found a book of bridges. A little drawing put a support beneath the middle of a long plank. It looked almost disappointingly simple. He fetched a scrap of wood and laid it across two stones to see why anyone had bothered to draw it.'''
        if s[child + ".attention_divisor"] == 1:
            text += ''' He had time to follow the explanation to its end.''' if child == "tansy" else ''' She read the explanation twice before returning to work.'''
        elif s[child + ".attention_divisor"] == 2:
            text += (''' The work bell interrupted halfway through. The picture stayed in memory, but part of the explanation did not.''' if child == "mira" else ''' A call for more bricks took him away before he reached the end of the page. He remembered the shape better than the instructions.''')
        else:
            text += (''' The overseer called for four different errands before a whole page could be read. The picture was memorable. The reason for its details was not yet clear.''' if child == "mira" else ''' Each time he found his place, someone called him away. By the fourth errand, he could remember the bridge but not quite how its parts worked together.''')
        revealed = [child + ".read", child + ".meme." + ("DrainCraft" if child == "mira" else "BridgeCraft")]
    elif name == "mentor":
        text = '''Mira brought her question to Wolf. He put a finger on the low end of the drawn channel.

“Water won't read the arrow,” he said. “You have to give it somewhere lower to go.”

She tipped a board slightly and watched a drop travel along it.'''
        if s["tansy.mentored"]:
            text += ''' Tansy brought his bridge drawing too. Wolf pressed a hoof against the unsupported middle, then slipped a stone beneath it. Both young pigs stayed for the short demonstration.'''
        else:
            text += ''' Tansy was still at his separate job. He did not hear the answer; being in the same building was not the same as joining the conversation.'''
        text += '''

Then the work bell called them away. A demonstration helped. It did not finish either job for them.'''
        revealed = ["mira.mentored", "tansy.mentored"]
    elif name == "practice_drain":
        if s["drain.works"]:
            text = '''Mira cut a trial channel beside a stack of bricks, giving it the fall the diagram required. When she poured in a bucket of water, it ran clear of the bottom course.

She looked at her dry hoof, then back at the book. “This is what I need at home.”'''
            text += ''' Tansy had held the bucket while she cut. Now he followed the little stream with her, checking where it ended.''' if s["valley.work_arrangement"] == "shared" else ''' She worked alone, and had to stop cutting whenever she fetched more water.'''
            text += '''

The pigs' names were on the palace notice. None of their names had shown her where to put that channel.'''
        else:
            text = '''Mira cut a channel that looked rather like the picture. She had missed how steeply it needed to fall. Her bucketful crept a little way, stopped, and soaked the bricks.

She moved one muddy hoof out of the puddle. “I haven't understood it yet.”

The work bell rang before she could try again. She put the book back with a strip of grass marking the unfinished page.'''
        revealed = ["drain.works", "mira.skilled"]
    elif name == "practice_bridge":
        if s["bridge.works"]:
            text = '''Tansy set a support beneath the long test plank before loading it with bricks. The plank held level. He took one brick off and put it back, as if the second success were a private answer to the first.

“We could mend the crossing with this.”'''
            text += ''' Mira had helped hold the plank while he placed the support. Together they lifted the test load down, using the same quiet signals they used for beams.''' if s["valley.work_arrangement"] == "shared" else ''' He unloaded the bricks alone. Mira was at the other end of the worksite and had not helped with this trial.'''
            text += '''

He wrote a small note beside the drawing. The page now held something he had checked for himself.'''
        else:
            text = '''Tansy set his plank on two end stones and piled bricks over the gap. He had copied the outline of the bridge without giving its middle enough support. The wood bowed; a brick slid into the dirt.

He took the load off slowly. The picture had made sense while he looked at it. Making it stand up was another matter. He kept the book open until the bell made him close it.'''
        revealed = ["bridge.works", "tansy.skilled"]
    elif name == "soup":
        text = '''At lunch Wolf brought his old pot up the hill and shared fish soup with Mira. There was a little dill left.

“You kept it all the way to the sea?” she asked.

“And back.”

She held the warm bowl while he wiped mortar from his sleeve. It was difficult to fit this tired builder inside the mouth drawn on the poster. Wolf did not ask her to decide anything about him before finishing her soup.'''
        revealed = ["soup.shared"]
    elif name == "paper":
        text = '''The brothers brought the newspaper to the worksite. Its headline congratulated them on their palace. Beneath it, the familiar wolf watched from the familiar drawing.

Mira and Tansy read the instruction to obey their elders. Old words could still make them lower their voices, even here among stones they had carried themselves. The pigs left the paper where the workers would pass it again.'''
        revealed = ["newspaper.read_again"]
    elif name == "finish":
        text = '''At last the roof was finished and the scaffolding came down. The tower could be seen from the market. The brothers climbed the steps in order of importance, disagreeing quietly about the order.

Inside, the books occupied the walls intended for portraits.'''
        if not s["mira.read"]:
            text += ''' Mira and Tansy had carried their weight in stone and timber, but the locked cupboards had never opened for them. The titles were still mostly titles.'''
        else:
            text += ''' Mira looked for the foundations volume; Tansy looked for the bridge drawing. Their unfinished thoughts were inside those covers.'''
        revealed = ["palace.roof"]
    elif name == "confrontation":
        text = '''“These were tools,” said the Third Little Pig. “Now we need the space. Take the books away.”

“A memorable opening ceremony,” said Fox from a window ledge.'''
        if s["mira.spoke"]:
            text += '''

Mira put a hoof against the foundations book. “No. I made its drain work. My cottage needs one.”'''
        if s["tansy.spoke"]:
            text += '''

Tansy stood beside the bridge volume. “And I tested this. We need it for the crossing.”'''
        if s["palace.coalition"]:
            text += '''

They looked at each other. Hold, the look meant. The same signal had kept a beam steady above their heads. Other workers gathered behind them.

“We built these shelves,” Mira said. “We can look after what is on them.”

The brothers faced a room that had begun to recognize its own work.'''
        elif s["palace.dissenters"]:
            text += '''

The protest hung in the room. They had worked under different overseers and had no shared signal for this. The brothers waited the voices out.

Mira loosened her grip, but did not put the foundations book back.'''
        else:
            text += '''

Mira opened her mouth, then shut it. Tansy watched the floor.''' + (''' Neither had been allowed to learn what the books could do.''' if not s["mira.read"] else ''' Neither could yet point to a successful trial of their own.''') + ''' The familiar instruction to obey came more readily than an answer.

The Third Little Pig repeated his order, louder this time.'''
        revealed = ["mira.spoke", "tansy.spoke", "palace.coalition", "palace.dissenters"]
    elif name == "ending":
        if s["palace.outcome"] == "library":
            text = '''The First Little Pig threatened to have everyone removed. Nobody helped him. The workers simply stayed between the brothers and the shelves.

The Third Little Pig wanted to remain important more than he wanted a struggle in front of the whole valley. He announced that the palace would be his magnificent gift to the public.

“And Wolf's cottage?” asked Mira.

The brother's smile tightened. He agreed that they would leave it too. The three pigs went down to their old brick house, arguing over whose idea the gift had been.

Upstairs, the workers carried the books back to the shelves. “Library,” someone suggested. They opened the doors before painting the name.

Wolf crossed the creek to his own cottage and lit the stove. This time the soup pot stayed on it. On the hill the windows shone around readers who no longer needed a pig's permission to turn a page. Fox settled by one of those windows, still hoping someone would bring lunch.'''
        elif s["palace.outcome"] == "night_school":
            text = '''The brothers had the books cleared from the hall and locked away. They did not notice one volume under Mira's work apron.

She carried it to the cracked brick house, where Wolf was still required to sleep. Tansy followed after dark. It was not their book by the pigs' rules, and it was certainly not a public library.

Wolf lit his little stove. Mira opened the foundations book on the table and made room for another pair of hooves. They began with the slope of a channel, speaking softly enough not to carry through the patched wall.

The palace remained the pigs' palace. The creek cottage remained occupied by the pigs. But beneath the old brick-house window, a thin line of lamplight reached the path, and three shadows leaned over one open page.'''
        else:
            text = '''The books went behind locked doors. The brothers chose places for their portraits and sent Wolf back to the brick house with tomorrow's building list.

They returned to his cottage by the creek for supper. The newspaper would describe the palace as another triumph. Fox watched them go. She had obtained her tower full of books; she had not obtained readers able to keep it.

Mira stopped inside the doorway before going home. Through the cupboard wire she could see a blue spine with a drawing of water on it. Beyond her reach, its gilt arrow pointed downhill. At her own doorstep, rainwater gathered in the same old place.'''
        revealed = ["palace.outcome", "palace.public", "palace.owner", "cottage.occupant",
                    "wolf.home_restored", "foundations.location", "books.accessible"]
    else:
        raise StoryError("Missing renderer: " + name)
    # All exposed state values exist at this episode; historical snapshots are
    # deliberately retained instead of consulting final state during narration.
    if any(key not in s for key in revealed):
        raise StoryError("Renderer exposes an unknown state key")
    blocks = text.split("\n\n")
    # Exposure is conservative and encounter-granular: only after the whole
    # performance has been read. Earlier paragraphs cannot reveal its conclusion.
    return [Paragraph(f"{name}.{i}", name, block.strip(), list(ep.event_ids),
                      list(revealed) if i == len(blocks) else [])
            for i, block in enumerate(blocks, 1)]


def narrate(episodes, params):
    return [para for ep in episodes for para in render(ep, params)]
