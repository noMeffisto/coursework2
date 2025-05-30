import syncedlyrics
import os
import mutagen
import re

def find_lrc_file(audio_file_path):
    """Tries to find an LRC file with the same name as the audio file."""
    base, _ = os.path.splitext(audio_file_path)
    lrc_path = base + ".lrc"
    print(f"LYRICS_DEBUG: Checking for LRC at: {lrc_path}")
    if os.path.exists(lrc_path):
        print(f"LYRICS_DEBUG: LRC file found: {lrc_path}")
        return lrc_path
    print(f"LYRICS_DEBUG: LRC file NOT found at: {lrc_path}")
    return None

def parse_lrc_content(lrc_content):
    """Parses LRC content and returns a list of (timestamp_ms, line)."""
    print(f"LYRICS_DEBUG: Entered parse_lrc_content. Content length: {len(lrc_content)}")
    if not lrc_content.strip():
        print("LYRICS_DEBUG: LRC content is empty or whitespace. Returning empty list.")
        return []
    
    parsed_lyrics = []
    # Regex to capture [mm:ss.xx] or [mm:ss.xxx]
    # .xx is centiseconds, .xxx is milliseconds.
    lrc_line_regex = re.compile(r'^\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)')

    try:
        # Ensure lrc_content is a string, not bytes
        if isinstance(lrc_content, bytes):
            print("LYRICS_DEBUG: LRC content was bytes, attempting to decode with utf-8.")
            try:
                lrc_content = lrc_content.decode('utf-8')
            except UnicodeDecodeError as ude:
                print(f"LYRICS_DEBUG: UTF-8 decode failed for LRC content: {ude}. Trying ISO-8859-1.")
                lrc_content = lrc_content.decode('iso-8859-1') # Common fallback

        for text_line in lrc_content.splitlines():
            match = lrc_line_regex.match(text_line)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                frac_seconds_str = match.group(3) # can be 'xx' or 'xxx'
                lyric_text = match.group(4).strip()

                # Convert fractional seconds to milliseconds
                if len(frac_seconds_str) == 2: # centiseconds
                    milliseconds_frac = int(frac_seconds_str) * 10
                else: # milliseconds (3 digits)
                    milliseconds_frac = int(frac_seconds_str)
                
                total_milliseconds = (minutes * 60 + seconds) * 1000 + milliseconds_frac
                
                if lyric_text: # Only add if there's actual text
                    parsed_lyrics.append((total_milliseconds, lyric_text))
            # else: # Optional: log lines that don't match the timecode format (e.g., metadata)
                # print(f"LYRICS_DEBUG: Skipped LRC line (no timecode or metadata): {text_line}")
        
        if parsed_lyrics:
            print(f"LYRICS_DEBUG: Successfully parsed LRC with custom parser, found {len(parsed_lyrics)} lines.")
            return sorted(parsed_lyrics)
        else:
            print(f"LYRICS_DEBUG: Custom parser found no valid lyric lines in LRC content.")
            return []

    except Exception as e:
        print(f"LYRICS_DEBUG: Error in custom parse_lrc_content: {e}")
        # import traceback # For more detailed errors during debugging
        # print(traceback.format_exc())
        return []


def get_lyrics(audio_file_path):
    """
    Attempts to load lyrics.
    Priority:
    1. Synced LRC file.
    2. Embedded unsynced lyrics from MP3 tags.

    Returns:
        tuple: (list_of_lyric_tuples, is_synced_flag)
               list_of_lyric_tuples: [(timestamp_ms, line), ...] or [(0, "full_text")]
               is_synced_flag: True if lyrics are from LRC, False otherwise.
    """
    print(f"LYRICS_DEBUG: Entered get_lyrics for: {audio_file_path}")
    lrc_file_path = find_lrc_file(audio_file_path)
    
    if lrc_file_path:
        print(f"LYRICS_DEBUG: Attempting to read LRC file: {lrc_file_path}")
        try:
            # Try with common encodings if utf-8 fails for LRC files
            content_read = False
            lrc_content = None
            encodings_to_try = ['utf-8', 'iso-8859-1', 'cp1251', 'cp1252'] # Add more if needed
            for enc in encodings_to_try:
                try:
                    with open(lrc_file_path, 'r', encoding=enc) as f:
                        lrc_content = f.read()
                    print(f"LYRICS_DEBUG: LRC content read successfully with encoding {enc}.")
                    print(f"LYRICS_DEBUG: LRC content (first 100 chars): {lrc_content[:100]}")
                    content_read = True
                    break 
                except UnicodeDecodeError:
                    print(f"LYRICS_DEBUG: Failed to decode LRC with {enc}.")
                    continue 
            
            if not content_read or lrc_content is None:
                print(f"LYRICS_DEBUG: Failed to read LRC content from {lrc_file_path} with tried encodings.")
                # Fall through to MP3 tags if reading failed completely

            else: # Content was read
                parsed_lrc = parse_lrc_content(lrc_content)
                print(f"LYRICS_DEBUG: Parsed LRC result (lines): {len(parsed_lrc) if parsed_lrc is not None else 'None'}")
                if parsed_lrc: # Check if list is not empty
                    print("LYRICS_DEBUG: Returning lyrics from LRC.")
                    return parsed_lrc, True 
                else:
                    print("LYRICS_DEBUG: LRC parsed but result was empty. Will try MP3 tags.")
        
        except IOError as ioe:
             print(f"LYRICS_DEBUG: IOError reading LRC file {lrc_file_path}: {ioe}")
        except Exception as e:
            print(f"LYRICS_DEBUG: Generic error reading or parsing LRC file {lrc_file_path}: {e}")
    else:
        print("LYRICS_DEBUG: LRC file not found by find_lrc_file.")

    print("LYRICS_DEBUG: Proceeding to check MP3 tags.")
    if audio_file_path.lower().endswith('.mp3'):
        print(f"LYRICS_DEBUG: Attempting to load lyrics from MP3 tags for: {audio_file_path}")
        try:
            audio = mutagen.File(audio_file_path, easy=False) 
            if audio is not None:
                unsynced_text = None
                found_text_in_tag = False

                # Print all available tags for debugging
                if hasattr(audio, 'tags') and audio.tags:
                    print(f"LYRICS_DEBUG: All tags found by mutagen (easy=False): {list(audio.tags.keys())}")
                else:
                    print("LYRICS_DEBUG: No 'tags' attribute or audio.tags is empty (easy=False).")

                # Try specific common USLT keys first
                # These keys might not exist directly if lang/desc are default empty strings
                # but mutagen might resolve them.
                uslt_keys_to_try = ['USLT::eng', 'USLT::XXX', 'USLT::'] 
                for key in uslt_keys_to_try:
                    if key in audio:
                        unsynced_text = audio[key].text
                        print(f"LYRICS_DEBUG: Found direct key '{key}'. Text length: {len(unsynced_text) if unsynced_text else 'None or 0'}. Text: '{unsynced_text[:100] if unsynced_text else ''}...' ")
                        if unsynced_text and unsynced_text.strip():
                            found_text_in_tag = True
                            break 
                    else:
                        print(f"LYRICS_DEBUG: Direct key '{key}' not found in audio object.")
                
                # If not found by direct keys, try iterating through all USLT frames
                if not found_text_in_tag and hasattr(audio, 'tags') and audio.tags:
                    uslt_frames = audio.tags.getall('USLT')
                    if uslt_frames:
                        print(f"LYRICS_DEBUG: Found {len(uslt_frames)} USLT frames via getall('USLT'). Iterating...")
                        for i, frame in enumerate(uslt_frames):
                            frame_text = frame.text
                            frame_lang = getattr(frame, 'lang', 'N/A')
                            frame_desc = getattr(frame, 'desc', 'N/A')
                            print(f"LYRICS_DEBUG: USLT Frame {i}: Lang='{frame_lang}', Desc='{frame_desc}', Text Length: {len(frame_text) if frame_text else 'None or 0'}. Text: '{frame_text[:100] if frame_text else ''}...' ")
                            if frame_text and frame_text.strip():
                                unsynced_text = frame_text
                                print(f"LYRICS_DEBUG: Using text from USLT Frame {i}.")
                                found_text_in_tag = True
                                break 
                    else:
                        print("LYRICS_DEBUG: No USLT frames found via getall('USLT').")
                
                # Fallback to easy=True if complex access failed or for other tags
                if not found_text_in_tag:
                    print("LYRICS_DEBUG: No text found via specific USLT keys or getall('USLT'). Trying easy=True for 'lyrics'.")
                    audio_easy = mutagen.File(audio_file_path, easy=True)
                    if audio_easy:
                        if hasattr(audio_easy, 'tags') and audio_easy.tags:
                             print(f"LYRICS_DEBUG: All tags found by mutagen (easy=True): {list(audio_easy.tags.keys())}")
                        else:
                            print("LYRICS_DEBUG: No 'tags' attribute or audio_easy.tags is empty (easy=True).")
                        
                        lyrics_tag_keys = ['lyrics', 'LYRICS'] # Common keys for lyrics in easy mode
                        for easy_key in lyrics_tag_keys:
                            if easy_key in audio_easy:
                                lyrics_value = audio_easy[easy_key]
                                # In easy mode, lyrics are often a list of strings
                                if isinstance(lyrics_value, list) and lyrics_value:
                                    unsynced_text = lyrics_value[0] # Take the first one
                                elif isinstance(lyrics_value, str):
                                    unsynced_text = lyrics_value
                                else:
                                    print(f"LYRICS_DEBUG: Tag '{easy_key}' (easy=True) found, but value is not a list or string, or is empty: {type(lyrics_value)}")
                                    continue

                                print(f"LYRICS_DEBUG: Found '{easy_key}' tag via easy=True. Text length: {len(unsynced_text) if unsynced_text else 'None or 0'}. Text: '{unsynced_text[:100] if unsynced_text else ''}...' ")
                                if unsynced_text and unsynced_text.strip():
                                    found_text_in_tag = True
                                    break
                            else:
                                print(f"LYRICS_DEBUG: Tag '{easy_key}' (easy=True) not found.")
                        if not found_text_in_tag:
                             print("LYRICS_DEBUG: No 'lyrics' or 'LYRICS' tag found via easy=True containing text.")
                    else:
                        print("LYRICS_DEBUG: mutagen.File (easy=True) returned None.")

                # Final check on unsynced_text
                if found_text_in_tag and unsynced_text and unsynced_text.strip():
                    print(f"LYRICS_DEBUG: Returning unsynced lyrics from MP3 tags (length: {len(unsynced_text.strip())}).")
                    return [(0, unsynced_text.strip())], False 
                else:
                    print("LYRICS_DEBUG: No valid/stripped unsynced text found in MP3 tags after all checks.")
            else:
                print("LYRICS_DEBUG: mutagen.File (easy=False) returned None for MP3 tags.")
        except Exception as e:
            print(f"LYRICS_DEBUG: Error reading MP3 tags from {audio_file_path}: {e}")

    print("LYRICS_DEBUG: No lyrics found from any source.")
    return [], False 