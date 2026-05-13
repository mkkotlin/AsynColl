import { Component, OnInit } from '@angular/core';
import { ApiService } from '../services/api.service';
import { DragDropModule, CdkDragDrop, moveItemInArray, transferArrayItem } from '@angular/cdk/drag-drop';
import { CommonModule } from '@angular/common'

@Component({
  selector: 'app-board',
  standalone: true,
  imports: [DragDropModule, CommonModule],
  templateUrl: './board.component.html'
})
export class BoardComponent implements OnInit {

  board: any;
  connectedLists: string[] = [];

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.api.getBoard(1).subscribe((data: any) => {
      this.board = data;

      // 🔥 Connect all lists using unique IDs
      this.connectedLists = this.board.lists.map(
        (list: any) => 'list-' + list.id
      );
    });
  }

  drop(event: CdkDragDrop<any[]>, targetList: any) {

    if (event.previousContainer === event.container) {
      // Same list reorder
      moveItemInArray(
        event.container.data,
        event.previousIndex,
        event.currentIndex
      );

    } else {
      // Cross-list movement
      transferArrayItem(
        event.previousContainer.data,
        event.container.data,
        event.previousIndex,
        event.currentIndex
      );

      const movedCard = event.container.data[event.currentIndex];

      // 🔥 Backend update
      this.api.updateCard(movedCard.id, {
        list: targetList.id,
        position: event.currentIndex
      }).subscribe();
    }
  }
}