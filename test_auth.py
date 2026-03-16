from ytmusicapi import YTMusic
import sys
import os

def test_auth():
    print("--- YTMusic Auth Test ---")
    if not os.path.exists("oauth.json"):
        print("ERROR: oauth.json not found in current directory.")
        return

    try:
        print("Initializing YTMusic with oauth.json...")
        yt = YTMusic("oauth.json")
        
        print("Testing: Requesting account info...")
        # This is a very basic call to check if the token is valid at all
        try:
            # Note: get_account_info might not be available in all versions or for all scopes
            # but we can try getting library playlists which is what failed before
            print("Testing: Requesting library playlists...")
            playlists = yt.get_library_playlists(limit=5)
            if playlists is None:
                print("RESULT: get_library_playlists returned None. This usually means the account has no playlists or the scope is restricted.")
            else:
                print(f"RESULT: Success! Found {len(playlists)} playlists.")
                for p in playlists:
                    print(f"  - {p['title']} ({p['playlistId']})")
            
            print("\nSUCCESS: Authentication seems to be working for library actions.")
            
        except Exception as e:
            print(f"inner ERROR: Call failed: {e}")
            
    except Exception as e:
        print(f"outer ERROR: Initialization failed: {e}")

if __name__ == "__main__":
    test_auth()
