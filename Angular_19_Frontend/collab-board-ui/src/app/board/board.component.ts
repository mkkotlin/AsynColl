import { Component, OnInit, OnDestroy } from '@angular/core';
import { ApiService } from '../services/api.service';
import { Router } from '@angular/router';
import {
  DragDropModule,
  CdkDragDrop,
  moveItemInArray,
  transferArrayItem
} from '@angular/cdk/drag-drop';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-board',
  standalone: true,
  imports: [DragDropModule, CommonModule],
  templateUrl: './board.component.html',
  styleUrl: './board.component.css'
})
export class BoardComponent implements OnInit, OnDestroy {
  board: any;
  boards: any[] = [];   // list of all boards for the dropdown
  currentBoardId: number = 1;  // tracks which board is active
  connectedLists: string[] = [];
  users: any[] = [];
  private socket!: WebSocket;
  loggedInUser = localStorage.getItem('username');


  constructor(private api: ApiService, private router: Router) { }

  ngOnInit(): void {
    this.connectWebSocket();
    this.loadBoards();   // populate dropdown first
    this.loadBoard(1);
    this.loadUsers();
  }

  ngOnDestroy(): void {
    this.socket?.close();
  }

  // Fetch all boards for the selector dropdown
  loadBoards(): void {
    this.api.getBoards().subscribe((data: any) => {
      this.boards = data;
    });
  }

  // Bridge between template event and loadBoard (cast not allowed in Angular templates)
  onBoardChange(event: Event): void {
    const id = Number((event.target as HTMLSelectElement).value);
    if (!id) return;
    this.currentBoardId = id;
    // Reconnect WebSocket to the newly selected board
    if (this.socket && this.socket.readyState !== WebSocket.CLOSED) {
      this.socket.onclose = () => this.connectWebSocket();
      this.socket.close();
    } else {
      this.connectWebSocket();
    }
    this.loadBoard(id);
  }

  // Fetch board data and map list IDs for drag-drop connectivity
  loadBoard(boardId: number | string): void {
    this.api.getBoard(+boardId).subscribe((data: any) => {
      this.board = data;
      this.connectedLists = this.board.lists.map((list: any) => 'list-' + list.id);
    });
  }

  // Fetch all available users for assignment dropdown
  loadUsers(): void {
    this.api.getUser().subscribe((data: any) => {
      this.users = data;
    });
  }

  // Connect WebSocket for real-time updates
  connectWebSocket(): void {
    this.socket = new WebSocket(`ws://127.0.0.1:8000/ws/board/${this.currentBoardId}/`);
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (['CARD_MOVED', 'CARD_ASSIGNED', 'CARD_CREATED'].includes(data.action)) {
        // Reload current board so activity log and card state are both fresh
        this.loadBoard(this.currentBoardId);
      }
    };
  }

  // Handle card drag-drop: same list reorder or cross-list move
  drop(event: CdkDragDrop<any[]>, targetList: any): void {
    const previousListId = event.previousContainer.id.split('-')[1];

    if (event.previousContainer === event.container) {
      // Same list: reorder cards
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
      const cardIds = event.container.data.map((c: any) => c.id);
      this.api.reorderList(targetList.id, cardIds).subscribe();
    } else {
      // Different list: move and reorder both lists
      transferArrayItem(
        event.previousContainer.data,
        event.container.data,
        event.previousIndex,
        event.currentIndex
      );

      const movedCard = event.container.data[event.currentIndex];
      this.api.updateCard(movedCard.id, { list: targetList.id }).subscribe(() => {
        const sourceCardIds = event.previousContainer.data.map((c: any) => c.id);
        const targetCardIds = event.container.data.map((c: any) => c.id);

        this.api.reorderList(+previousListId, sourceCardIds).subscribe();
        this.api.reorderList(targetList.id, targetCardIds).subscribe(() => {
          // Backend now pushes CARD_MOVED via channel_layer — no need to send from client
        });
      });
    }
  }

  // Assign card to selected user
  assignUser(card: any, event: Event): void {
    const select = event.target as HTMLSelectElement;
    const userId = Number(select.value);

    this.api.updateCard(card.id, { assigned_to_id: userId }).subscribe(() => {
      // Backend now pushes CARD_ASSIGNED via channel_layer — no need to send from client
    });
  }

  // Clear auth tokens and navigate to login
  logout(): void {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    this.socket.close();
    this.router.navigate(['/login']);
  }

  // Create new card in list
  createCard(listId: number, title: string, inputElement: HTMLInputElement): void {
    if (!title.trim()) return;
    this.api.createCard({ list: listId, title: title.trim() }).subscribe(() => {
      inputElement.value = '';
      // Backend now pushes CARD_CREATED via channel_layer — no need to send from client
    });
  }
}