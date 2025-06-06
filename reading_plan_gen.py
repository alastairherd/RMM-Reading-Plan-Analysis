import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict, deque

# --- Configuration: Define the Books for Each Reading Track ---
TRACKS_CONFIG = {
    "History": [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
        "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther"
    ],
    "Wisdom": [
        "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Songs"
    ],
    "Prophets": [
        "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
        "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum",
        "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi"
    ],
    "NewTestament": [
        "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
        "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", "Philippians",
        "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy",
        "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter",
        "1 John", "2 John", "3 John", "Jude", "Revelation"
    ]
}

def get_verse_word_counts(bible_path='Bible-kjv-1611'):
    """
    Parses the Bible JSON files to get a word count for every single verse.
    
    Args:
        bible_path (str): The directory containing the Bible JSON files.

    Returns:
        list: A list of dictionaries, each representing a single verse.
              Returns None if the directory is not found.
    """
    if not os.path.exists(bible_path):
        print(f"Error: The directory '{bible_path}' was not found.")
        print("Please ensure the Bible data is in the correct location.")
        return None

    all_verses = []
    # Ensure a canonical order by sorting the filenames from the config
    all_books_in_order = [book for track in TRACKS_CONFIG.values() for book in track]
    
    for book_name in all_books_in_order:
        filename = f"{book_name}.json"
        filepath = os.path.join(bible_path, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                book_data = json.load(f)
                for chapter in book_data['chapters']:
                    for verse in chapter['verses']:
                        all_verses.append({
                            "book": book_name,
                            "chapter": chapter['chapter'],
                            "verse": verse['verse'],
                            "words": len(verse['text'].split())
                        })
    return all_verses

def get_track_for_book(book_name):
    """Helper function to find which track a book belongs to."""
    for track, books in TRACKS_CONFIG.items():
        if book_name in books:
            return track
    return None

def format_passages(passages):
    """
    Condenses a list of verse dictionaries into formatted passage strings.
    This function can handle ranges within chapters and across chapters.
    e.g., [Genesis 1:1, 1:2, 1:3] -> "Genesis 1:1-3"
    """
    if not passages:
        return []

    # Group verses by book and chapter first
    grouped = defaultdict(list)
    for p in passages:
        grouped[(p['book'], p['chapter'])].append(p['verse'])

    # Sort books and chapters canonically for the final output string
    track_order = ["History", "Wisdom", "Prophets", "NewTestament"]
    book_order_map = {book: i for i, book in enumerate([b for t in track_order for b in TRACKS_CONFIG.get(t, [])])}
    sorted_keys = sorted(grouped.keys(), key=lambda k: (book_order_map.get(k[0], 999), k[1]))

    # Build the formatted passage strings
    formatted_strings = []
    for book, chap in sorted_keys:
        verses = sorted(grouped[(book, chap)])
        if not verses: continue

        start_verse = verses[0]
        end_verse = verses[0]
        for i in range(1, len(verses)):
            # If the verse is consecutive, extend the range
            if verses[i] == end_verse + 1:
                end_verse = verses[i]
            # Otherwise, finalize the previous range and start a new one
            else:
                if start_verse == end_verse:
                    formatted_strings.append(f"{book} {chap}:{start_verse}")
                else:
                    formatted_strings.append(f"{book} {chap}:{start_verse}-{end_verse}")
                start_verse = end_verse = verses[i]
        
        # Add the last range for the current chapter
        if start_verse == end_verse:
            formatted_strings.append(f"{book} {chap}:{start_verse}")
        else:
            formatted_strings.append(f"{book} {chap}:{start_verse}-{end_verse}")
            
    return formatted_strings


def generate_balanced_plan(tracks_config, all_verses_data):
    """
    The main algorithm for generating the balanced reading plan.
    This version includes a corrected rollback mechanism to prevent unnatural breaks.
    """
    total_words = sum(v['words'] for v in all_verses_data)
    print(f"Total words in the Bible: {total_words}")
    ideal_daily_target = total_words / 365
    print(f"Ideal target daily word count: {ideal_daily_target:.0f}\n")

    # --- 1. Setup tracks and their data ---
    verses_by_track = {track_name: [] for track_name in tracks_config}
    for verse in all_verses_data:
        verses_by_track[get_track_for_book(verse['book'])].append(verse)

    track_iterators = {name: iter(verses) for name, verses in verses_by_track.items()}
    track_total_words = {name: sum(v['words'] for v in verses) for name, verses in verses_by_track.items()}
    track_words_read = {name: 0 for name in tracks_config}
    
    # This deque holds verses that have been rolled back and must be read first.
    rolled_back_verses = {name: deque() for name in tracks_config}
    
    final_plan = {}
    daily_word_totals = []
    words_read_so_far = 0
    
    # --- 2. Build plan day by day for 365 days ---
    for day_index in range(365):
        day_passages = []
        words_today = 0

        # --- a. Calculate a strongly self-correcting daily target ---
        ideal_total_at_end_of_today = ideal_daily_target * (day_index + 1)
        current_daily_target = ideal_total_at_end_of_today - words_read_so_far
        
        # --- b. Fill the day's readings verse by verse ---
        while words_today < current_daily_target:
            best_track_to_pull_from = None
            max_deficit = -float('inf')
            target_progress_ratio = (day_index + 1) / 365
            
            for track_name in tracks_config.keys():
                # A track is available if it has rolled-back verses or its main iterator is not empty
                if not rolled_back_verses[track_name] and track_iterators[track_name] is None: continue
                if track_total_words.get(track_name, 0) == 0: continue
                
                current_progress = track_words_read[track_name] / track_total_words[track_name]
                deficit = target_progress_ratio - current_progress
                if deficit > max_deficit:
                    max_deficit = deficit
                    best_track_to_pull_from = track_name
            if best_track_to_pull_from is None: break

            # Correctly get the next verse, prioritizing the rolled-back buffer
            verse_to_add = None
            if rolled_back_verses[best_track_to_pull_from]:
                verse_to_add = rolled_back_verses[best_track_to_pull_from].popleft()
            elif track_iterators[best_track_to_pull_from]:
                try:
                    verse_to_add = next(track_iterators[best_track_to_pull_from])
                except StopIteration:
                    track_iterators[best_track_to_pull_from] = None # Exhausted
                    continue
            
            if verse_to_add:
                day_passages.append(verse_to_add)
                words_today += verse_to_add['words']
                track_words_read[best_track_to_pull_from] += verse_to_add['words']

        # --- c. Polishing Step: Rollback Short Fragments ---
        if day_passages:
            last_verse = day_passages[-1]
            verses_in_last_chapter = [v for v in day_passages if v['book'] == last_verse['book'] and v['chapter'] == last_verse['chapter']]
            
            ROLLBACK_THRESHOLD = 3 
            is_short_fragment = len(verses_in_last_chapter) <= ROLLBACK_THRESHOLD
            words_in_fragment = sum(v['words'] for v in verses_in_last_chapter)
            day_would_be_too_short = (words_today - words_in_fragment) < (ideal_daily_target * 0.75)

            if is_short_fragment and not day_would_be_too_short:
                verses_to_roll_back = verses_in_last_chapter
                day_passages = [v for v in day_passages if v not in verses_to_roll_back]
                
                # Prepend to the deque to be read first on the next iteration
                for verse in reversed(verses_to_roll_back):
                    rolled_back_verses[get_track_for_book(verse['book'])].appendleft(verse)
                
                for verse in verses_to_roll_back:
                    track_words_read[get_track_for_book(verse['book'])] -= verse['words']
                
                words_today = sum(v['words'] for v in day_passages)

        # --- d. Finalize day's readings ---
        day_of_year = pd.to_datetime('2025-01-01') + pd.to_timedelta(day_index, unit='d')
        day_key = day_of_year.strftime('%m%d')
        final_plan[day_key] = format_passages(day_passages)
        daily_word_totals.append(words_today)
        words_read_so_far += words_today
        
    return final_plan, daily_word_totals

def main():
    """
    Main function to generate the plan, save it, and show its statistics.
    """
    print("--- Generating New Verse-Accurate Balanced Reading Plan ---")
    
    all_verses_data = get_verse_word_counts()
    if all_verses_data is None:
        return

    balanced_plan, daily_word_totals = generate_balanced_plan(TRACKS_CONFIG, all_verses_data)
    
    output_filename = 'balanced_reading_plan.json'
    with open(output_filename, 'w') as f:
        json.dump(balanced_plan, f, indent=4)
    print(f"\n[+] Successfully generated and saved the plan to '{output_filename}'")

    df_new = pd.DataFrame({'WordCount': daily_word_totals})
    
    print("\n--- Statistics for the New Balanced Plan ---")
    print(df_new['WordCount'].describe())

    # Generate and save a plot to visualize the new plan's consistency
    plt.figure(figsize=(12, 6))
    plt.plot(df_new.index, df_new['WordCount'], label='Daily Word Count (New Plan)', color='darkgreen', linewidth=1.5)
    plt.axhline(y=df_new['WordCount'].mean(), color='firebrick', linestyle='--', label=f"Mean: {df_new['WordCount'].mean():.0f}")
    plt.title('Daily Word Counts for the New Verse-Accurate Balanced Plan')
    plt.xlabel('Day of the Year')
    plt.ylabel('Number of Words')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.ylim(bottom=0, top=df_new['WordCount'].max() * 1.1)
    
    output_plot_filename = 'balanced_plan_distribution.png'
    plt.savefig(output_plot_filename)
    print(f"\n[+] A plot of the new plan's distribution has been saved to '{output_plot_filename}'")
    plt.show()

if __name__ == '__main__':
    main()
