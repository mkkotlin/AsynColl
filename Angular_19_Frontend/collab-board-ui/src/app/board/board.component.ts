import { Component, OnInit, OnDestroy } from '@angular/core';
import { ApiService } from '../services/api.service';
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
  templateUrl: './board.component.html'
})
export class BoardComponent implements OnInit, OnDestroy {

  board: any;
  connectedLists: string[] = [];
  users: any[] = [];
  private socket!: WebSocket;

constructor(private api: ApiService) {}

  ngOnInit(): void {
    // this.connectWebSocket();
    // this.loadBoard();
    // this.loadUsers();
    this.api.login({
      username: 'mayank',
      password:'mayank'
    }).subscribe((res: any)=>{
      localStorage.setItem('access', res.access);
      localStorage.setItem('refresh', res.refresh);
      console.log('JWT stored');
          this.connectWebSocket();
    this.loadBoard();
    this.loadUsers();
    })
  }

  ngOnDestroy(): void {
    this.socket?.close();
  }

  loadBoard() {
    this.api.getBoard(1).subscribe((data: any) => {
      this.board = data;

      this.connectedLists = this.board.lists.map(
        (list: any) => 'list-' + list.id
      );
    });
  }

  loadUsers(){
    this.api.getUser().subscribe((data: any)=>{
      this.users = data;
    })
  }

  connectWebSocket() {
    this.socket = new WebSocket('ws://127.0.0.1:8000/ws/board/1/');

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.action === 'CARD_MOVED' || data.action === 'CARD_ASSIGNED') {
        this.loadBoard();
      }
    };
  }

  // 🔥 FINAL DROP LOGIC
  drop(event: CdkDragDrop<any[]>, targetList: any) {

    const previousListId = event.previousContainer.id.split('-')[1];
    const currentListId = event.container.id.split('-')[1];

    if (event.previousContainer === event.container) {

      // Same list reorder
      moveItemInArray(
        event.container.data,
        event.previousIndex,
        event.currentIndex
      );

      const updatedCards = event.container.data;
      const cardIds = updatedCards.map((c: any) => c.id);

      this.api.reorderList(targetList.id, cardIds).subscribe(() => {
        this.socket.send(JSON.stringify({ action: 'CARD_MOVED' }));
      });

    } else {

      // Cross list move
      transferArrayItem(
        event.previousContainer.data,
        event.container.data,
        event.previousIndex,
        event.currentIndex
      );

      const movedCard = event.container.data[event.currentIndex];

      // Update card list
      this.api.updateCard(movedCard.id, {
        list: targetList.id
      }).subscribe(() => {

        const sourceCards = event.previousContainer.data;
        const targetCards = event.container.data;

        // Reorder both lists
        this.api.reorderList(+previousListId, sourceCards.map(c => c.id)).subscribe();
        this.api.reorderList(targetList.id, targetCards.map(c => c.id)).subscribe(() => {

          this.socket.send(JSON.stringify({ action: 'CARD_MOVED' }));

        });

      });
    }
  }

  assignUser(card: any, event: Event){
    const select = event.target as HTMLSelectElement;
    const userId = Number(select.value)
    console.log('Assign clicked')
    this.api.updateCard(card.id, {
      assigned_to_id: userId
    }).subscribe(()=>{
      console.log('api response')
      this.socket.send(JSON.stringify({
        action: "CARD_ASSIGNED",
        cardId: card.id,
        userId: userId
      }))
    })
  }
}