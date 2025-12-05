import socket
import hashlib
import os
import sys
import random
import time

BUFFER_SIZE = 1024

def generate_nonce(length=32):
    """Generates a cryptographically secure random number."""
    return os.urandom(length)

def commit(data):
    """Returns SHA-256 hash of the data."""
    return hashlib.sha256(data).hexdigest()

def calculate_dice_sum(seed, num_dice, player_id):
    """Derives dice rolls deterministically from the shared seed.
    player_id: 0 for Server (Alice), 1 for Client (Bob) to ensure distinct rolls"""
    random.seed(int.from_bytes(seed, 'big') + player_id)
    rolls = [random.randint(1, 6) for _ in range(num_dice)]
    return rolls, sum(rolls)

def play_match(conn, is_server, k_dice, n_rounds):
    my_wins = 0
    opponent_wins = 0
    
    print(f"\n--- STARTING MATCH: {k_dice} Dice, {n_rounds} Rounds ---")

    for i in range(1, n_rounds + 1):
        print(f"\n[Round {i}]")
        
        my_nonce = generate_nonce()
        my_commitment = commit(my_nonce)
        
        if is_server:
            conn.sendall(my_commitment.encode())
            opponent_commitment = conn.recv(BUFFER_SIZE).decode()
        else:
            opponent_commitment = conn.recv(BUFFER_SIZE).decode()
            conn.sendall(my_commitment.encode())
            
        print(f"   > Commitments exchanged.")
        
        if is_server:
            conn.sendall(my_nonce)
            opponent_nonce = conn.recv(BUFFER_SIZE)
        else:
            opponent_nonce = conn.recv(BUFFER_SIZE)
            conn.sendall(my_nonce)
            
        if commit(opponent_nonce) != opponent_commitment:
            print("   !!! CHEATING DETECTED: Hash mismatch! Aborting.")
            return

        shared_seed = bytes(a ^ b for a, b in zip(my_nonce, opponent_nonce))
        
        # Determine rolls (Server is ID 0, Client is ID 1)
        # Note: We use the SAME seed to ensure we both agree on the numbers
        # but we shift the seed slightly by ID so Alice and Bob get different dice.
        server_rolls, server_sum = calculate_dice_sum(shared_seed, k_dice, 0)
        client_rolls, client_sum = calculate_dice_sum(shared_seed, k_dice, 1)

        print(f"   > Shared Seed derived.")
        
        if is_server:
            my_r, my_s = server_rolls, server_sum
            opp_r, opp_s = client_rolls, client_sum
            role = "Alice (Server)"
        else:
            my_r, my_s = client_rolls, client_sum
            opp_r, opp_s = server_rolls, server_sum
            role = "Bob (Client)"
            
        print(f"   > {role} Rolls: {my_r} (Sum: {my_s})")
        print(f"   > Opponent Rolls: {opp_r} (Sum: {opp_s})")

        if my_s > opp_s:
            print("   > RESULT: You Win this round!")
            my_wins += 1
        elif my_s < opp_s:
            print("   > RESULT: Opponent Wins this round.")
            opponent_wins += 1
        else:
            print("   > RESULT: Draw.")

    print("\n--- MATCH ENDED ---")
    print(f"Final Score -> You: {my_wins} | Opponent: {opponent_wins}")
    if my_wins > opponent_wins:
        print("WINNER: YOU")
    elif my_wins < opponent_wins:
        print("WINNER: OPPONENT")
    else:
        print("RESULT: DRAW")

def main():
    if len(sys.argv) < 2:
        print("Usage: python game_node.py [server|client]")
        return

    mode = sys.argv[1]
    HOST = '0.0.0.0'
    PORT = 65432

    if mode == 'server':
        try:
            k = int(input("Enter number of dice (k): "))
            n = int(input("Enter number of rounds: "))
        except ValueError:
            print("Invalid input, defaulting to k=2, n=3")
            k, n = 2, 3

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            print(f"Alice listening on {PORT}...")
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                config = f"{k},{n}"
                conn.sendall(config.encode())
                play_match(conn, True, k, n)

    elif mode == 'client':
        SERVER_IP = os.getenv('SERVER_IP', '127.0.0.1')
        print(f"Bob is looking for Alice at {SERVER_IP}:{PORT}...")
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((SERVER_IP, PORT))
                    print("Bob connected to Alice!")

                    data = s.recv(BUFFER_SIZE).decode()
                    if not data:
                        print("connection closed by server")
                        break

                    config = data.split(",")
                    k = int(config[0])
                    n = int(config[1])
                    play_match(s, False, k, n)
                    break

            except (ConnectionRefusedError, OSError):
                print("Alice is not ready yet (still inputting config?). Retrying in 2s...")
                time.sleep(2)
            except Exception as e:
                print(f"Unexpected error: {e}")
                break

if __name__ == "__main__":
    main()