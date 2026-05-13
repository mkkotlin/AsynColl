import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  // url to get data from backend "api"
 private baseUrl = 'http://127.0.0.1:8000/api';

 constructor(private http:HttpClient){}

//  getBoard data
getBoard(id:number){
  return this.http.get(`${this.baseUrl}/boards/${id}/`);
}

// update card drag-drop
updateCard(id: number, data: any) {
  return this.http.patch(`${this.baseUrl}/cards/${id}/`, data);
}
}
