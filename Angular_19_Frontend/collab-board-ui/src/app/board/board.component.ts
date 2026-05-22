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
  connectedLists: string[] = [];
  users: any[] = [];
  private socket!: WebSocket;
  loggedInUser = localStorage.getItem('username');
 

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit(): void {
    this.connectWebSocket();
    this.loadBoard();
    this.loadUsers();
  }

  ngOnDestroy(): void {
    this.socket?.close();
  }

  // Fetch board data and map list IDs for drag-drop connectivity
  loadBoard(): void {
    this.api.getBoard(1).subscribe((data: any) => {
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
    this.socket = new WebSocket('ws://127.0.0.1:8000/ws/board/1/');
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (['CARD_MOVED', 'CARD_ASSIGNED', 'CARD_CREATED'].includes(data.action)) {
        this.loadBoard();
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
      this.api.reorderList(targetList.id, cardIds).subscribe(() => {
        this.socket.send(JSON.stringify({ action: 'CARD_MOVED' }));
      });
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
          this.socket.send(JSON.stringify({ action: 'CARD_MOVED' }));
        });
      });
    }
  }

  // Assign card to selected user
  assignUser(card: any, event: Event): void {
    const select = event.target as HTMLSelectElement;
    const userId = Number(select.value);

    this.api.updateCard(card.id, { assigned_to_id: userId }).subscribe(() => {
      this.socket.send(JSON.stringify({ action: 'CARD_ASSIGNED', cardId: card.id, userId }));
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
      this.socket.send(JSON.stringify({ action: 'CARD_CREATED' }));
      this.loadBoard();
    });
  }
}