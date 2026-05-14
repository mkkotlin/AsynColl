import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private baseUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) {}

  getBoard(id: number) {
    return this.http.get(`${this.baseUrl}/boards/${id}/`);
  }

  updateCard(id: number, data: any) {
    return this.http.patch(`${this.baseUrl}/cards/${id}/`, data);
  }

  // 🔥 NEW
  reorderList(listId: number, cardIds: number[]) {
    return this.http.post(
      `${this.baseUrl}/lists/${listId}/reorder/`,
      { card_ids: cardIds }
    );
  }
  getUser(){
    return this.http.get(`${this.baseUrl}/users/`);
  }
}